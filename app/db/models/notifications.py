from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# NOTIFICATION MODEL


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_details_id = Column(UUID(as_uuid=True))
    img = Column(String)
    action = Column(String)

    proposal_id = Column(UUID(as_uuid=True))
    transaction_id = Column(String)

    href = Column(String)
    additional_text = Column(String)

    date = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean)
