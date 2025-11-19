import typing as t

from pydantic import BaseModel


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


class Price(BaseModel):
    price: float
    t: int
