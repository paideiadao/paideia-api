from pydantic import BaseModel
import uuid
import typing as t
import datetime

### SCHEMAS FOR ACTIVITIES ###


class ActivityConstants:
    # categories
    PROPOSAL_CATEGORY = "Proposals"
    COMMENT_CATEGORY = "Comments"
    # actions
    CREATED_DISCUSSION = "created"
    EDITED_DISCUSSION = "edited"
    LIKED_DISCUSSION = "liked"
    DISLIKED_DISCUSSION = "disliked"
    REMOVED_LIKE_DISCUSSION = "removed a like from"
    FOLLOWED_DISCUSSION = "followed"
    UNFOLLOWED_DISCUSSION = "unfollowed"
    COMMENT = "made a comment on"
    LIKED_COMMENT = "liked a comment on"
    DISLIKE_COMMENT = "disliked a comment on"
    REMOVED_LIKE_COMMENT = "removed a like from a comment on"
    ADDED_ADDENDUM = "added an addendum"
    # secondary
    ADDENDUM_PR = "to the proposal"


class CreateOrUpdateActivity(BaseModel):
    user_details_id: uuid.UUID
    action: t.Optional[str]
    value: t.Optional[str]
    secondary_action: t.Optional[str]
    secondary_value: t.Optional[str]
    category: t.Optional[str]
    link: t.Optional[str]


class Activity(CreateOrUpdateActivity):
    id: uuid.UUID
    date: datetime.datetime

    class Config:
        orm_mode = True


class vwActivity(Activity):
    name: t.Optional[str]
    img_url: t.Optional[str]
