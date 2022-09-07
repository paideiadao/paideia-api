import typing as t
import random
from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse

from db.session import get_db
from db.schemas.proposal import Proposal, CreateProposal, LikeProposalRequest, FollowProposalRequest, UpdateProposalBasic, CreateOrUpdateComment, CreateOrUpdateAddendum, AddReferenceRequest
from db.crud.proposals import (
    get_proposal_by_id,
    get_proposals_by_dao_id,
    get_comment_by_id,
    create_new_proposal,
    delete_proposal_by_id,
    set_likes_by_proposal_id,
    set_likes_by_comment_id,
    set_followers_by_proposal_id,
    edit_proposal_basic_by_id,
    add_commment_by_proposal_id,
    add_addendum_by_proposal_id,
    add_reference_by_proposal_id
)
from core.auth import get_current_active_user, get_current_active_superuser
from websocket.connection_manager import connection_manager

proposal_router = r = APIRouter()


@r.get(
    "/by_dao_id/{dao_id}",
    response_model=t.List[Proposal],
    response_model_exclude_none=True,
    name="proposals:all-proposals"
)
def get_proposals(dao_id: int, db=Depends(get_db)):
    try:
        return get_proposals_by_dao_id(db, dao_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.get(
    "/{proposal_id}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:proposal"
)
def get_proposal(proposal_id: int, db=Depends(get_db)):
    try:
        proposal = get_proposal_by_id(db, proposal_id)
        if not proposal:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="proposal not found")
        return proposal
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.post(
    "/",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:create-proposal"
)
def create_proposal(proposal: CreateProposal, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        if proposal.user_id == user.id:
            return create_new_proposal(db, proposal)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/{proposal_id}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:edit-proposal"
)
def edit_proposal(proposal_id: int, proposal: UpdateProposalBasic, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        proposal = edit_proposal_basic_by_id(
            db, user.id, proposal_id, proposal)
        if not proposal:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="proposal not found")
        return proposal
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/like/{proposal_id}",
    name="proposals:like-proposal"
)
def like_proposal(proposal_id: int, req: LikeProposalRequest, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        if req.user_id == user.id:
            return set_likes_by_proposal_id(db, proposal_id, req.user_id, req.type)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/follow/{proposal_id}",
    name="proposals:follow-proposal"
)
def follow_proposal(proposal_id: int, req: FollowProposalRequest, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        if req.user_id == user.id:
            return set_followers_by_proposal_id(db, proposal_id, req.user_id, req.type)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/comment/{proposal_id}",
    name="proposals:comment-proposal"
)
async def comment_proposal(proposal_id: int, comment: CreateOrUpdateComment, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        if comment.user_id == user.id:
            ret = add_commment_by_proposal_id(db, proposal_id, comment)
            comment_dict = get_comment_by_id(db, ret.id).dict()
            comment_dict["date"] = str(comment_dict["date"])
            await connection_manager.send_personal_message_by_substring_matcher(
                "proposal_comments_" + str(proposal_id),
                {
                    "proposal_id": proposal_id,
                    "comment": comment_dict,
                }
            )
            return ret
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/comment/like/{comment_id}",
    name="proposals:like-proposal-comment"
)
def like_comment(comment_id: int, req: LikeProposalRequest, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        if req.user_id == user.id:
            return set_likes_by_comment_id(db, comment_id, req.user_id, req.type)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/addendum/{proposal_id}",
    name="proposals:addendum-proposal"
)
def create_addendum_proposal(proposal_id: int, addendum: CreateOrUpdateAddendum, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        addendum = add_addendum_by_proposal_id(
            db, user.id, proposal_id, addendum
        )
        if not addendum:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
        return addendum
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/reference/{proposal_id}",
    name="proposals:reference-proposal"
)
def reference_proposal(proposal_id: int, req: AddReferenceRequest, db=Depends(get_db), user=Depends(get_current_active_user)):
    try:
        reference = add_reference_by_proposal_id(
            db, user.id, proposal_id, req.referred_proposal_id
        )
        if not reference:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized")
        return reference
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.delete(
    "/{proposal_id}",
    response_model=Proposal,
    response_model_exclude_none=True,
    name="proposals:delete-proposal"
)
def delete_proposal(proposal_id: int, db=Depends(get_db), user=Depends(get_current_active_superuser)):
    try:
        proposal = delete_proposal_by_id(db, proposal_id)
        if not proposal:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="proposal not found")
        return proposal
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
