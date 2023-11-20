import uuid
from pydantic import BaseModel

import typing as t
import datetime

### SCHEMAS FOR BLOGS ###


class BlogConfig(BaseModel):
    add_to_highlights: bool = False
    add_to_education_page: bool = False


class CreateOrUpdateBlog(BaseModel):
    name: str
    img_url: t.Optional[str]
    description: t.Optional[str]
    content: t.Optional[str]
    category: t.Optional[str]
    additional_details: BlogConfig


class Blog(CreateOrUpdateBlog):
    id: uuid.UUID
    link: str
    date: datetime.datetime

    class Config:
        orm_mode = True
