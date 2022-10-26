from pydantic import BaseModel
import typing as t


class CreateAndUpdateFaq(BaseModel):
    question: str
    answer: t.Optional[str]
    tags: t.List[str] = []


class Faq(CreateAndUpdateFaq):
    id: int

    class Config:
        orm_mode = True
