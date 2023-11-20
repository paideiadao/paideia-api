import uuid
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
    ADD_STAKE_TRANSACTION_SUBMITTED = "add stake transaction submitted"
    ADD_STAKE_TRANSACTION_CONFIRMED = "add stake transaction confirmed"
    REMOVE_STAKE_TRANSACTION_SUBMITTED = "remove stake transaction submitted"
    REMOVE_STAKE_TRANSACTION_CONFIRMED = "remove stake transaction confirmed"
    CREATE_PROPOSAL_TRANSACTION_SUBMITTED = "create proposal transaction submitted"
    CREATE_PROPOSAL_TRANSACTION_CONFIRMED = "create proposal transaction confirmed"
    VOTE_TRANSACTION_SUBMITTED = "vote transaction submitted"
    VOTE_TRANSACTION_CONFIRMED = "vote transaction confirmed"


class CreateAndUpdateNotification(BaseModel):
    user_details_id: uuid.UUID
    img: t.Optional[str]
    action: t.Optional[str]
    proposal_id: t.Optional[uuid.UUID]
    transaction_id: t.Optional[str]
    href: t.Optional[str]
    additional_text: t.Optional[str]
    is_read: bool = False


class Notification(CreateAndUpdateNotification):
    id: uuid.UUID
    proposal_name: t.Optional[str]
    date: datetime.datetime

    class Config:
        orm_mode = True
