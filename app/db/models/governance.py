from sqlalchemy import Boolean, Column, Integer, String, Float

from db.session import Base

# GOVERNANCE MODEL


class Governance(Base):
    __tablename__ = "governances"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    governance_id = Column(Integer)
    user_id = Column(Integer)
