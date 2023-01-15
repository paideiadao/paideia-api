from pydantic import BaseModel
import datetime
import typing as t


class NotificationConstants:
    # actions
    COMMENT_REPLY = "replied to your comment on the discussion"
    COMMENT_LIKE = "liked your comoment on the discussion"
    LIKED_DISCUSSION = "liked the discussion"
    FOLLOW_DISCUSSION = "followed the discussion"
    COMMENTED_ON_DISCUSSION = "commented on the discussion"


class CreateAndUpdateNotification(BaseModel):
    user_details_id: int
    img: t.Optional[str]
    action: t.Optional[str]
    proposal_id: t.Optional[int]
    transaction_id: t.Optional[str]
    href: t.Optional[str]
    additional_text: t.Optional[str]
    is_read: bool = False


class Notification(CreateAndUpdateNotification):
    id: int
    proposal_name: t.Optional[str]
    date: datetime.datetime

    class Config:
        orm_mode = True
