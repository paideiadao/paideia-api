from sqlalchemy import Boolean, Column, Integer, String, Float
import uuid
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# GOVERNANCE MODEL


class Governance(Base):
    __tablename__ = "governances"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_id = Column(Integer)
    is_optimistic = Column(Boolean)
    is_quadratic_voting = Column(Boolean)
    time_to_challenge__sec = Column(Integer)
    quorum = Column(Integer)
    vote_duration__sec = Column(Integer)
    amount = Column(Float)
    currency = Column(String)
    support_needed = Column(Integer)


class GovernanceWhitelist(Base):
    __tablename__ = "governance_whitelist"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    governance_id = Column(Integer)
    ergo_address_id = Column(Integer)
