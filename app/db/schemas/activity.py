from pydantic import BaseModel

import typing as t
import datetime

### SCHEMAS FOR ACTIVITIES ###


class ActivityConstants:
    # categories
    PROPOSAL_CATEGORY = "Proposals"
    COMMENT_CATEGORY = "Comments"
    # actions
    CREATED_DISCUSSION = "created the discussion"
    EDITED_DISCUSSION = "edited the disccussion"
    LIKED_DISCUSSION = "liked the discussion"
    DISLIKED_DISCUSSION = "disliked the discussion"
    REMOVED_LIKE_DISCUSSION = "removed like from the discussion"
    FOLLOWED_DISCUSSION = "followed the discussion"
    UNFOLLOWED_DISCUSSION = "unfollowed the discussion"
    COMMENT = "made a comment on the proposal"
    ADDED_ADDENDUM = "added an addendum"
    # secondary
    ADDENDUM_PR = "to the proposal"


class CreateOrUpdateActivity(BaseModel):
    user_details_id: int
    img_url: t.Optional[str]
    action: t.Optional[str]
    value: t.Optional[str]
    secondary_action: t.Optional[str]
    secondary_value: t.Optional[str]
    category: t.Optional[str]


class Activity(CreateOrUpdateActivity):
    id: int
    date: datetime.datetime

    class Config:
        orm_mode = True
