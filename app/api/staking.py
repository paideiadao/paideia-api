import time
import typing as t
import uuid

from fastapi import APIRouter, Depends, status
from db.schemas.staking import AddStakeRequest, DaoStakeInfo, GetStakeRequest, ParticipationInfo, Profit, ProfitInfo, StakeInfo, StakeKeyInfo, StakeKeyInfoWithParticipation, NewStakeRecord, StakeRequest, UnstakeRequest
from db.schemas.util import SigningRequest
from db.session import get_db
from paideia_state_client import staking
from db.crud.dao import get_dao
from db.crud.users import get_ergo_addresses_by_user_id, get_primary_wallet_address_by_user_id
from ergo.indexed_node_client import get_balance, get_token_info
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
    
@r.post(
    "/add",
    response_model=SigningRequest,
    response_model_exclude_none=True,
    name="staking:add_stake",
)
def stake(
    req: AddStakeRequest,
    db=Depends(get_db),
):
    try:
        dao = get_dao(db, req.dao_id)
        token_info = get_token_info(dao.tokenomics.token_id)
        main_address = get_primary_wallet_address_by_user_id(db, req.user_id)
        all_addresses = list(map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, req.user_id)))
        unsignedTransaction = staking.add_stake(dao.dao_key, req.stake_key, int(req.amount*(10**token_info["decimals"])), main_address, all_addresses)
        return SigningRequest(
            message="Add to your stake in this dao",
            unsigned_transaction=unsignedTransaction
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
    
@r.put(
    "/",
    response_model=SigningRequest,
    response_model_exclude_none=True,
    name="staking:remove_stake",
)
def stake(
    req: UnstakeRequest,
    db=Depends(get_db),
):
    try:
        if req.new_stake_key_info.locked_until/1000 > time.time() and req.new_stake_key_info.stake == 0:
            raise Exception("Stake locked due to voting")
        current_stake = get_stake(GetStakeRequest(req.dao_id, req.user_id), db)
        for key in current_stake.stake_keys:
            if key.key_id == req.new_stake_key_info.key_id and key.stake > req.new_stake_key_info.stake and req.new_stake_key_info.stake > 0:
                raise Exception("Partial staking not allowed")
        dao = get_dao(db, req.dao_id)
        token_info = get_token_info(dao.tokenomics.token_id)
        main_address = get_primary_wallet_address_by_user_id(db, req.user_id)
        all_addresses = list(map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, req.user_id)))
        rewards = []
        for profit in req.new_stake_key_info.profit:
            if len(profit.token_id)>0:
                profit_token_info = get_token_info(profit.token_id)
                rewards.append(int(profit.amount*(10**profit_token_info["decimals"])))
            else:
                rewards.append(int(profit.amount*(10**9)))
        newStakeRecord = NewStakeRecord(
            stake=int(req.new_stake_key_info.stake*(10**token_info["decimals"])),
            lockedUntil=req.new_stake_key_info.locked_until,
            rewards=rewards
        )
        unsignedTransaction = staking.unstake(dao.dao_key, req.new_stake_key_info.key_id, newStakeRecord, main_address, all_addresses)
        return SigningRequest(
            message="Remove tokens from your stake and/or profit in this dao",
            unsigned_transaction=unsignedTransaction
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
    
@r.get(
    "/dao_stake_info/{dao_id}",
    response_model=DaoStakeInfo,
    response_model_exclude_none=True,
    name="staking:get_dao_stake"
)
def get_dao_stake(
    dao_id: uuid.UUID,
    db=Depends(get_db)
):
    try:
        dao = get_dao(db, dao_id)
        token_info = get_token_info(dao.tokenomics.token_id)
        stakeInfo = staking.get_dao_stake(dao.dao_key)
        profit = []
        profit.append(Profit(token_info["token_name"], dao.tokenomics.token_id, stakeInfo["profit"][0]/10**token_info["decimals"]))
        profit.append(Profit("Erg", "", stakeInfo["profit"][1]/10**9))
                    
        return DaoStakeInfo(
            dao_id=dao_id,
            total_staked=stakeInfo["totalStaked"]/10**token_info["decimals"],
            stakers=stakeInfo["stakers"],
            voted=stakeInfo["voted"],
            voted_total=stakeInfo["votedTotal"],
            next_emission=stakeInfo["nextEmission"],
            profit=profit
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}') 
    
@r.post(
    "/user_stake_info",
    response_model=StakeInfo,
    response_model_exclude_none=True,
    name="staking:get_stake"
)
def get_stake(
    req: GetStakeRequest,
    db=Depends(get_db)
):
    try:
        dao = get_dao(db, req.dao_id)
        token_info = get_token_info(dao.tokenomics.token_id)
        all_addresses = list(map(lambda ea: ea.address, get_ergo_addresses_by_user_id(db, req.user_id)))
        stake_keys = []
        for addr in all_addresses:
            user_balance = get_balance(addr)
            for token in user_balance["confirmed"]["tokens"]:
                if " Stake Key" in token["name"]:
                    stakeKeyInfo = staking.get_stake(dao.dao_key, token["tokenId"])
                    if stakeKeyInfo:
                        participation_info = ParticipationInfo(
                                proposals_voted_on=stakeKeyInfo["participationRecord"]["voted"],
                                total_voting_power_used=stakeKeyInfo["participationRecord"]["votedTotal"]
                            ) if "participationRecord" in stakeKeyInfo else ParticipationInfo(
                            proposals_voted_on=0,total_voting_power_used=0)
                        ergProfit = stakeKeyInfo["stakeRecord"]["rewards"][0]
                        tokenProfit = stakeKeyInfo["stakeRecord"]["rewards"][1:]
                        profit = [ProfitInfo(
                            token_name="Erg",
                            token_id="",
                            amount=ergProfit/(10**9)
                        )]
                        for i in range(len(tokenProfit)):
                            profit_token_info = get_token_info(stakeKeyInfo["profitTokens"][i])
                            profit.append(ProfitInfo(
                                token_name=profit_token_info["name"],
                                token_id=stakeKeyInfo["profitTokens"][i],
                                amount=tokenProfit[i]/(10**profit_token_info["decimals"])
                            ))
                        stake_keys.append(StakeKeyInfoWithParticipation(
                            key_id=token["tokenId"],
                            locked_until=stakeKeyInfo["stakeRecord"]["lockedUntil"],
                            participation_info=participation_info,
                            stake=stakeKeyInfo["stakeRecord"]["stake"]/(10**token_info["decimals"]),
                            profit=profit
                        ))
        return StakeInfo(
            dao_id=req.dao_id,
            user_id=req.user_id,
            stake_keys=stake_keys
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}') 
