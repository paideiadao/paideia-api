from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from db.session import Base

# NOTIFICATION MODEL


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_details_id = Column(Integer)
    img = Column(String)
    action = Column(String)

    proposal_id = Column(Integer)
    transaction_id = Column(String)

    href = Column(String)
    additional_text = Column(String)

    date = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean)
