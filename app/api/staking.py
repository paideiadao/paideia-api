import typing as t

from fastapi import APIRouter, Depends, status
from db.schemas.staking import StakeRequest
from db.schemas.util import SigningRequest
from db.session import get_db
from paideia_state_client import staking
from db.crud.dao import get_dao
from db.crud.users import get_ergo_addresses_by_user_id, get_primary_wallet_address_by_user_id
from ergo.indexed_node_client import get_token_info
from starlette.responses import JSONResponse

staking_router = r = APIRouter()

@r.post(
    "/",
    response_model=SigningRequest,
    response_model_exclude_none=True,
    name="staking:stake",
)
def stake(
    req: StakeRequest,
    db=Depends(get_db),
):
    try:
        dao = get_dao(db, req.dao_id)
        token_info = get_token_info(dao.tokenomics.token_id)
        main_address = get_primary_wallet_address_by_user_id(db, req.user_id)
        all_addresses = list(map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, req.user_id)))
        unsignedTransaction = staking.stake(dao.dao_key, int(req.amount*(10**token_info["decimals"])), main_address, all_addresses)
        return SigningRequest(
            message="Stake tokens to this dao",
            unsigned_transaction=unsignedTransaction
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
    
# @r.post(
#     "/",

# )