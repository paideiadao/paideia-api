import typing as t
import random
import uuid

from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse

from api.notifications import notification_create
from paideia_state_client import staking, dao, proposals
from db.schemas.util import SigningRequest
from db.session import get_db
from db.schemas.activity import CreateOrUpdateActivity, ActivityConstants
from db.schemas.notifications import CreateAndUpdateNotification, NotificationConstants
from db.schemas.proposal import (
    CreateOnChainProposal,
    Proposal,
    CreateProposal,
    LikeProposalRequest,
    FollowProposalRequest,
    SendFundsAction,
    UpdateProposalBasic,
    CreateOrUpdateComment,
    CreateOrUpdateAddendum,
    AddReferenceRequest,
    VoteRequest,
    CreateOnChainProposalResponse
)
from db.crud.dao import get_dao
from db.crud.proposals import (
    get_proposal_by_id,
    get_proposal_by_slug,
    get_proposals_by_dao_id,
    get_proposals_by_user_id,
    get_comment_by_id,
    create_new_proposal,
    delete_proposal_by_id,
    set_likes_by_proposal_id,
    set_likes_by_comment_id,
    set_followers_by_proposal_id,
    edit_proposal_basic_by_id,
    add_commment_by_proposal_id,
    delete_comment_by_comment_id,
    add_addendum_by_proposal_id,
    add_reference_by_proposal_id,
)
from db.crud.activity_log import create_user_activity
from db.crud.notifications import generate_action
from db.crud.users import get_ergo_addresses_by_user_id, get_primary_wallet_address_by_user_id, get_user_details_by_id, get_user, get_user_profile
from core.async_handler import run_coroutine_in_sync
from core.auth import get_current_active_user, get_current_active_superuser
from websocket.connection_manager import connection_manager
from util.util import is_uuid

from config import Config, Network


proposal_router = r = APIRouter()

def proposal_status(status_code: int) -> str:
    match status_code:
        case -2: 
            return "Failed - Quorum"
        case -1:
            return "Active"
        case 0:
            return "Failed - Vote"
        case 1:
            return "Passed"
        case _:
            return "Unknown"

@r.get(
    "/by_dao_id/{dao_id}",
    response_model=t.List[Proposal],
    response_model_exclude_none=True,
    name="proposals:all-proposals",
)
def get_proposals(dao_id: uuid.UUID, db=Depends(get_db)):
    try:
        db_proposals = get_proposals_by_dao_id(db, dao_id)
        db_dao = get_dao(db, dao_id)
        state_proposals = dao.get_proposals(db_dao.dao_key)
        for p in state_proposals:
            db_proposal = None
            for dbp in db_proposals:
                if dbp.on_chain_id == p["proposalIndex"] and dbp.name == p["proposalName"]:
                    db_proposal = dbp
            if db_proposal is None:
                proposal = proposals.get_proposal(
                    db_dao.dao_key, p["proposalIndex"])
                create_proposal(db=db, user=get_user(db, Config[Network].admin_id), proposal=CreateProposal(
                    dao_id=dao_id,
                    user_details_id=get_user_profile(
                        db, Config[Network].admin_id, dao_id).id,
                    name=proposal["proposal"]["name"],
                    voting_system=proposal["proposalType"],
                    actions=proposal["proposal"]["actions"],
                    is_proposal=True,
                    box_height=0,
                    on_chain_id=p["proposalIndex"],
                    votes=proposal["proposal"]["votes"],
                    attachments=[],
                    status=proposal_status(proposal["proposal"]["passed"]) 
                ))
            elif db_proposal.box_height < p["proposalHeight"]:
                proposal = proposals.get_proposal(
                    db_dao.dao_key, p["proposalIndex"])
                edit_proposal_basic_by_id(db=db, user_details_id=db_proposal.user_details_id, id=db_proposal.id, proposal=UpdateProposalBasic(
                    box_height=p["proposalHeight"],
                    dao_id=db_proposal.dao_id,
                    user_details_id=db_proposal.user_details_id,
                    name=db_proposal.name,
                    votes=proposal["proposal"]["votes"],
                    attachments=db_proposal.attachments,
                    status=proposal_status(proposal["proposal"]["passed"]) 
                ))

        return get_proposals_by_dao_id(db, dao_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.get(
    "/by_user_details_id/{user_details_id}",
    response_model_exclude_none=True,
    name="proposals:user-proposals",
)
def get_user_proposals(user_details_id: uuid.UUID, db=Depends(get_db)):
    try:
        basic_proposals = get_proposals_by_user_id(db, user_details_id)
        return list(map(lambda x: get_proposal_by_id(db, x.id), basic_proposals))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.get(
    "/{proposal_slug}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:proposal",
)
def get_proposal(proposal_slug: str, db=Depends(get_db)):
    try:
        if is_uuid(proposal_slug):
            return get_proposal_by_id(db, uuid.UUID(proposal_slug))
        else:
            return get_proposal_by_slug(db, proposal_slug)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.post(
    "/",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:create-proposal",
)
def create_proposal(
    proposal: CreateProposal, db=Depends(get_db), user=Depends(get_current_active_user)
):
    try:
        user_details_id = proposal.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        proposal = create_new_proposal(db, proposal)
        # add to activities
        if type(proposal) != JSONResponse:
            activity = CreateOrUpdateActivity(
                user_details_id=user_details_id,
                action=ActivityConstants.CREATED_DISCUSSION,
                value=proposal.name,
                category=ActivityConstants.PROPOSAL_CATEGORY,
            )
            create_user_activity(db, user_details_id, activity)
        return proposal
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


def validate_action(actions: t.List[dict]):
    sendFundsActions = []
    updateConfigActions = []

    for action in actions:
        if action["actionType"] == "SendFundsBasic":
            SendFundsAction.validate(action["action"])
            action["action"]["repeats"] = 0
            action["action"]["repeatDelay"] = 0
            sendFundsActions.append(action["action"])
        else:
            raise Exception("Unknown action type")

    return sendFundsActions, updateConfigActions


@r.post(
    "/on_chain_proposal",
    response_model=CreateOnChainProposalResponse,
    response_model_exclude_none=True,
    name="proposals:create-proposal",
)
def create_on_chain_proposal(
    proposal: CreateOnChainProposal, db=Depends(get_db), user=Depends(get_current_active_user)
):
    try:
        db_dao = get_dao(db, proposal.dao_id)
        user_details_id = proposal.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        sendFundsActions, updateConfigActions = validate_action(
            proposal.actions)

        main_address = get_primary_wallet_address_by_user_id(db, user.id)
        all_addresses = list(
            map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, user.id)))
        current_proposal_list = dao.get_proposals(db_dao.dao_key)
        new_proposal_index = len(current_proposal_list)
        proposal.on_chain_id = new_proposal_index
        proposal.box_height = 0

        unsigned_tx = proposals.create_proposal(
            db_dao.dao_key, proposal.name, proposal.stake_key, main_address, all_addresses, proposal.end_time, sendFundsActions)

        proposal = create_new_proposal(db, proposal)
        # add to activities
        if type(proposal) != JSONResponse:
            activity = CreateOrUpdateActivity(
                user_details_id=user_details_id,
                action=ActivityConstants.CREATED_DISCUSSION,
                value=proposal.name,
                category=ActivityConstants.PROPOSAL_CATEGORY,
            )
            create_user_activity(db, user_details_id, activity)
        return CreateOnChainProposalResponse(
            message="Sign message to create proposal",
            unsigned_transaction=unsigned_tx,
            proposal=proposal
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.post(
    "/vote",
    response_model=SigningRequest,
    response_model_exclude_none=True,
    name="proposals:vote"
)
def vote(
    voteRequest: VoteRequest, db=Depends(get_db), user=Depends(get_current_active_user)
):
    try:
        db_dao = get_dao(db, voteRequest.dao_id)
        main_address = get_primary_wallet_address_by_user_id(db, user.id)
        all_addresses = list(
            map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, user.id)))
        db_proposal = get_proposal_by_id(db, voteRequest.proposal_id)
        stake_info = staking.get_stake(db_dao.dao_key, voteRequest.stake_key)
        if stake_info["stakeRecord"]["stake"] < sum(voteRequest.votes):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Can not vote for more than staked amount")
        if len(db_proposal.votes) != len(voteRequest.votes):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Vote array should be same size as proposal vote array")
        unsigned_tx = proposals.cast_vote(db_dao.dao_key, voteRequest.stake_key,
                                          db_proposal.on_chain_id, voteRequest.votes, main_address, all_addresses)
        return SigningRequest(
            message="Sign to vote on the proposal",
            unsigned_transaction=unsigned_tx
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/{proposal_id}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:edit-proposal",
)
def edit_proposal(
    proposal_id: uuid.UUID,
    proposal: UpdateProposalBasic,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        _proposal = get_proposal_by_id(db, proposal_id)
        if type(_proposal) == JSONResponse:
            return _proposal
        user_details = get_user_details_by_id(db, _proposal.user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        proposal = edit_proposal_basic_by_id(
            db, _proposal.user_details_id, proposal_id, proposal
        )
        # add to activities
        if type(proposal) != JSONResponse:
            activity = CreateOrUpdateActivity(
                user_details_id=_proposal.user_details_id,
                action=ActivityConstants.EDITED_DISCUSSION,
                value=proposal.name,
                category=ActivityConstants.PROPOSAL_CATEGORY,
            )
            create_user_activity(db, _proposal.user_details_id, activity)
        return proposal
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/like/{proposal_id}", name="proposals:like-proposal")
def like_proposal(
    proposal_id: uuid.UUID,
    req: LikeProposalRequest,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        user_details_id = req.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        likes = set_likes_by_proposal_id(
            db, proposal_id, user_details_id, req.type)
        # add to activities and notifier
        if type(likes) != JSONResponse:
            proposal = get_proposal_by_id(db, proposal_id)
            # activity logging
            action = {
                "like": ActivityConstants.LIKED_DISCUSSION,
                "dislike": ActivityConstants.DISLIKED_DISCUSSION,
                "remove": ActivityConstants.REMOVED_LIKE_DISCUSSION,
            }
            activity = CreateOrUpdateActivity(
                user_details_id=user_details_id,
                action=action[req.type],
                value=proposal.name,
                category=ActivityConstants.PROPOSAL_CATEGORY,
            )
            create_user_activity(db, user_details_id, activity)
            # notifications
            if req.type == "like" and proposal.user_details_id != user_details_id:
                notification = CreateAndUpdateNotification(
                    user_details_id=proposal.user_details_id,
                    action=generate_action(
                        user_details.name, NotificationConstants.LIKED_DISCUSSION
                    ),
                    proposal_id=proposal.id,
                )
                # handle async web sockets stuff
                run_coroutine_in_sync(
                    notification_create(
                        proposal.user_details_id, notification, db, current_user=None
                    )
                )
        return likes
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/follow/{proposal_id}", name="proposals:follow-proposal")
def follow_proposal(
    proposal_id: uuid.UUID,
    req: FollowProposalRequest,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        user_details_id = req.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        followers = set_followers_by_proposal_id(
            db, proposal_id, req.user_details_id, req.type
        )
        # add to activities and notifier
        if type(followers) != JSONResponse:
            proposal = get_proposal_by_id(db, proposal_id)
            # activity logging
            action = {
                "follow": ActivityConstants.FOLLOWED_DISCUSSION,
                "unfollow": ActivityConstants.UNFOLLOWED_DISCUSSION,
            }
            activity = CreateOrUpdateActivity(
                user_details_id=user_details_id,
                action=action[req.type],
                value=proposal.name,
                category=ActivityConstants.PROPOSAL_CATEGORY,
            )
            create_user_activity(db, user_details_id, activity)
            # notifications
            if req.type == "follow" and proposal.user_details_id != user_details_id:
                notification = CreateAndUpdateNotification(
                    user_details_id=proposal.user_details_id,
                    action=generate_action(
                        user_details.name, NotificationConstants.FOLLOW_DISCUSSION
                    ),
                    proposal_id=proposal.id,
                )
                # handle async web sockets stuff
                run_coroutine_in_sync(
                    notification_create(
                        proposal.user_details_id, notification, db, current_user=None
                    )
                )
        return followers
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/comment/{proposal_id}", name="proposals:comment-proposal")
async def comment_proposal(
    proposal_id: uuid.UUID,
    comment: CreateOrUpdateComment,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        user_details_id = comment.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )

        ret = add_commment_by_proposal_id(db, proposal_id, comment)
        comment_dict = get_comment_by_id(db, ret.id).dict()
        comment_dict["date"] = str(comment_dict["date"])
        if type(comment_dict) == JSONResponse:
            return comment_dict
        # web sockets
        await connection_manager.send_personal_message_by_substring_matcher(
            "proposal_comments_" + str(proposal_id),
            {
                "proposal_id": proposal_id,
                "comment": comment_dict,
            },
        )
        # add to activities and notifier
        proposal = get_proposal_by_id(db, proposal_id)
        # activity logging
        activity = CreateOrUpdateActivity(
            user_details_id=user_details_id,
            action=ActivityConstants.COMMENT,
            value=proposal.name,
            category=ActivityConstants.COMMENT_CATEGORY,
        )
        create_user_activity(db, user_details_id, activity)
        # notifications
        if proposal.user_details_id != user_details_id:
            notification = CreateAndUpdateNotification(
                user_details_id=proposal.user_details_id,
                action=generate_action(
                    user_details.name, NotificationConstants.COMMENTED_ON_DISCUSSION
                ),
                proposal_id=proposal.id,
            )
            await notification_create(
                proposal.user_details_id, notification, db, current_user=None
            )
        if "parent" in comment_dict and comment_dict["parent"] != None:
            parent_comment_id = comment_dict["parent"]
            parent_user_details_id = get_comment_by_id(
                db, parent_comment_id
            ).user_details_id
            if parent_user_details_id != user_details_id:
                notification = CreateAndUpdateNotification(
                    user_details_id=parent_user_details_id,
                    action=generate_action(
                        user_details.name, NotificationConstants.COMMENT_REPLY
                    ),
                    proposal_id=proposal.id,
                )
                await notification_create(
                    parent_user_details_id, notification, db, current_user=None
                )
        return comment_dict
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.delete("/comment/{comment_id}", name="proposals:delete-comment-proposal")
async def delete_comment_proposal(
    comment_id: uuid.UUID,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        comment = get_comment_by_id(db, comment_id)
        if type(comment) == JSONResponse:
            return comment
        user_details_id = comment.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return delete_comment_by_comment_id(db, comment_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/comment/like/{comment_id}", name="proposals:like-proposal-comment")
def like_comment(
    comment_id: uuid.UUID,
    req: LikeProposalRequest,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        user_details_id = req.user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        likes = set_likes_by_comment_id(
            db, comment_id, user_details_id, req.type)
        # add to activities and notifier
        if type(likes) != JSONResponse:
            comment = get_comment_by_id(db, comment_id)
            proposal = get_proposal_by_id(db, comment.proposal_id)
            # activity logging
            action = {
                "like": ActivityConstants.LIKED_COMMENT,
                "dislike": ActivityConstants.DISLIKE_COMMENT,
                "remove": ActivityConstants.REMOVED_LIKE_COMMENT,
            }
            if req.type == "like":
                activity = CreateOrUpdateActivity(
                    user_details_id=user_details_id,
                    action=action[req.type],
                    value=proposal.name,
                    category=ActivityConstants.COMMENT_CATEGORY,
                )
                create_user_activity(db, user_details_id, activity)
            # notifications
            if req.type == "like" and proposal.user_details_id != user_details_id:
                notification = CreateAndUpdateNotification(
                    user_details_id=proposal.user_details_id,
                    action=generate_action(
                        user_details.name, NotificationConstants.COMMENT_LIKE
                    ),
                    proposal_id=proposal.id,
                )
                # handle async web sockets stuff
                run_coroutine_in_sync(
                    notification_create(
                        proposal.user_details_id, notification, db, current_user=None
                    )
                )
            return likes
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/addendum/{proposal_id}", name="proposals:addendum-proposal")
def create_addendum_proposal(
    proposal_id: uuid.UUID,
    addendum: CreateOrUpdateAddendum,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        proposal = get_proposal_by_id(db, proposal_id)
        if type(proposal) == JSONResponse:
            return proposal
        user_details = get_user_details_by_id(db, proposal.user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        addendum = add_addendum_by_proposal_id(
            db, proposal.user_details_id, proposal_id, addendum
        )
        if type(addendum) == JSONResponse:
            return addendum
        addendum_dict = {
            "id": addendum.id,
            "proposal_id": addendum.proposal_id,
            "name": addendum.name,
            "content": addendum.content,
            "date": str(addendum.date),
        }
        # add to activitites
        activity = CreateOrUpdateActivity(
            user_details_id=proposal.user_details_id,
            action=ActivityConstants.ADDED_ADDENDUM,
            value=addendum.name,
            secondary_action=ActivityConstants.ADDENDUM_PR,
            secondary_value=proposal.name,
            category=ActivityConstants.PROPOSAL_CATEGORY,
        )
        create_user_activity(db, proposal.user_details_id, activity)
        return addendum_dict
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put("/reference/{proposal_id}", name="proposals:reference-proposal")
def reference_proposal(
    proposal_id: uuid.UUID,
    req: AddReferenceRequest,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    try:
        proposal = get_proposal_by_id(db, proposal_id)
        if type(proposal) == JSONResponse:
            return proposal
        user_details = get_user_details_by_id(db, proposal.user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        reference = add_reference_by_proposal_id(
            db, proposal.user_details_id, proposal_id, req.referred_proposal_id
        )
        return reference
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.delete(
    "/{proposal_id}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:delete-proposal",
)
def delete_proposal(
    proposal_id: uuid.UUID, db=Depends(get_db), user=Depends(get_current_active_user)
):
    try:
        proposal = get_proposal_by_id(db, proposal_id)
        if type(proposal) == JSONResponse:
            return proposal
        user_details = get_user_details_by_id(db, proposal.user_details_id)
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return delete_proposal_by_id(db, proposal_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.websocket("/ws/{proposal_id}")
async def websocket_endpoint(websocket: WebSocket, proposal_id: str):
    random_key = "proposal_comments_" + \
        proposal_id + "_" + str(random.random())
    await connection_manager.connect(random_key, websocket)
    try:
        while True:
            # pause loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(random_key)
