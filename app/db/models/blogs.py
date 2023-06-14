import uuid
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from db.session import Base

# BLOG MODEL


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String)
    link = Column(String)
    img_url = Column(String)
    description = Column(String)
    content = Column(String)
    category = Column(String)
    additional_details = Column(JSON)
    date = Column(DateTime(timezone=True), server_default=func.now())
