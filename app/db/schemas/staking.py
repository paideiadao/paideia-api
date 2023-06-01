import uuid
from pydantic import BaseModel

import typing as t

class StakeRequest(BaseModel):
    dao_id: uuid.UUID
    amount: float
    user_id: uuid.UUID

class GetStakeRequest(BaseModel):
    dao_id: uuid.UUID
    user_id: uuid.UUID

