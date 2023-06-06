import uuid
from pydantic import BaseModel

import typing as t

class StakeRequest(BaseModel):
    dao_id: uuid.UUID
    amount: float
    user_id: uuid.UUID

class AddStakeRequest(StakeRequest):
    stake_key: str

class GetStakeRequest(BaseModel):
    dao_id: uuid.UUID
    user_id: uuid.UUID

class ParticipationInfo(BaseModel):
    proposals_voted_on: int
    total_voting_power_used: int

class ProfitInfo(BaseModel):
    token_name: str
    token_id: str
    amount: float

class StakeKeyInfo(BaseModel):
    key_id: str
    locked_until: int
    stake: float
    profit: t.List[ProfitInfo]

class StakeKeyInfoWithParticipation(StakeKeyInfo):
    participation_info: ParticipationInfo

class StakeInfo(BaseModel):
    dao_id: uuid.UUID
    user_id: uuid.UUID
    stake_keys: t.List[StakeKeyInfoWithParticipation]

class UnstakeRequest(BaseModel):
    dao_id: uuid.UUID
    user_id: uuid.UUID
    new_stake_key_info: StakeKeyInfo

class NewStakeRecord(BaseModel):
    stake: int
    lockedUntil: int
    rewards: t.List[int]


