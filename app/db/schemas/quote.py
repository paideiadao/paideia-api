from pydantic import BaseModel
import typing as t


class CreateAndUpdateQuote(BaseModel):
    quote: str
    author: t.Optional[str]
    show: bool = True


class Quote(CreateAndUpdateQuote):
    id: int

    class Config:
        orm_mode = True
