from sqlalchemy import Column, Integer, String, Boolean
import uuid
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# QUOTE MODEL


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    quote = Column(String)
    author = Column(String)
    show = Column(Boolean)
