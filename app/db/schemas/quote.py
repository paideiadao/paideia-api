import uuid
from pydantic import BaseModel
import typing as t


class CreateAndUpdateQuote(BaseModel):
    quote: str
    author: t.Optional[str]
    show: bool = True


class Quote(CreateAndUpdateQuote):
    id: uuid.UUID

    class Config:
        orm_mode = True
