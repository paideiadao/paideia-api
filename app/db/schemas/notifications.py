from pydantic import BaseModel
import datetime
import typing as t


class CreateAndUpdateNotification(BaseModel):
    user_id: int
    img: t.Optional[str]
    action: t.Optional[str]
    proposal_id: t.Optional[int]
    transaction_id: t.Optional[str]
    href: t.Optional[str]
    additional_text: t.Optional[str]
    is_read: bool = False


class Notification(CreateAndUpdateNotification):
    id: int
    date: datetime.datetime

    class Config:
        orm_mode = True
