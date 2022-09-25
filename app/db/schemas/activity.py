from pydantic import BaseModel

import typing as t
import datetime

### SCHEMAS FOR ACTIVITIES ###


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
