import typing as t
import random
import uuid

from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse

from api.notifications import notification_create
from db.session import get_db
from db.schemas.activity import CreateOrUpdateActivity, ActivityConstants
from db.schemas.notifications import CreateAndUpdateNotification, NotificationConstants
from db.schemas.proposal import (
    Proposal,
    CreateProposal,
    LikeProposalRequest,
    FollowProposalRequest,
    UpdateProposalBasic,
    CreateOrUpdateComment,
    CreateOrUpdateAddendum,
    AddReferenceRequest,
)
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
from db.crud.users import get_user_details_by_id
from core.async_handler import run_coroutine_in_sync
from core.auth import get_current_active_user, get_current_active_superuser
from websocket.connection_manager import connection_manager

proposal_router = r = APIRouter()


@r.get(
    "/by_dao_id/{dao_id}",
    response_model=t.List[Proposal],
    response_model_exclude_none=True,
    name="proposals:all-proposals",
)
def get_proposals(dao_id: uuid.UUID, db=Depends(get_db)):
    try:
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
        if '-' in proposal_slug:
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
        likes = set_likes_by_proposal_id(db, proposal_id, user_details_id, req.type)
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
        likes = set_likes_by_comment_id(db, comment_id, user_details_id, req.type)
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
    random_key = "proposal_comments_" + proposal_id + "_" + str(random.random())
    await connection_manager.connect(random_key, websocket)
    try:
        while True:
            # pause loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(random_key)
