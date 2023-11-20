import uuid
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# FAQ MODEL


class Faq(Base):
    __tablename__ = "faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    question = Column(String)
    answer = Column(String)
    tags = Column(JSON)
