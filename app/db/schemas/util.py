import uuid
from pydantic import BaseModel

import typing as t

class SigningRequest(BaseModel):
    message: str
    unsigned_transaction: dict

class TokenAmount(BaseModel):
    token_name: str
    amount: float

class Transaction(BaseModel):
    transaction_id: str
    label: str
    amount: t.List[TokenAmount]
    time: int

class TransactionHistory(BaseModel):
    transactions: t.List[Transaction]
