import uuid
from pydantic import BaseModel

import typing as t

class SigningRequest(BaseModel):
    message: str
    unsigned_transaction: dict
