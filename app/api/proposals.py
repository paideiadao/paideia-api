import typing as t
from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from db.session import get_db
from db.schemas.proposal import Proposal, CreateProposal
from db.crud.proposals import (
    get_proposal,
    get_proposals_by_dao_id,
    create_new_proposal
)
from core.auth import get_current_active_user, get_current_active_superuser

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
def get_proposal_by_id(proposal_id: int, db=Depends(get_db)):
    try:
        proposal = get_proposal(db, proposal_id)
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
