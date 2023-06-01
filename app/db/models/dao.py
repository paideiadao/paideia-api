import uuid
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# DAO MODEL


class Dao(Base):
    __tablename__ = "daos"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_key = Column(String)
    config_height = Column(Integer)
    dao_name = Column(String)
    dao_short_description = Column(String)
    dao_url = Column(String)
    is_draft = Column(Boolean)
    is_published = Column(Boolean)
    nav_stage = Column(Integer)
    is_review = Column(Boolean)
    category = Column(String)
    created_dtz = Column(DateTime(timezone=True), server_default=func.now())


class HighlightedDaos(Base):
    __tablename__ = "project_highlights"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_id = Column(UUID(as_uuid=True))


class vw_daos(Base):
    __tablename__ = "vw_daos"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_key = Column(String)
    config_height = Column(Integer)
    dao_name = Column(String)
    dao_url = Column(String)
    dao_short_description = Column(String)
    category = Column(Boolean)
    created_dtz = Column(DateTime(timezone=True))
    logo_url = Column(String)
    token_id = Column(String)
    token_ticker = Column(String)
    member_count = Column(Integer)
    proposal_count = Column(Integer)
