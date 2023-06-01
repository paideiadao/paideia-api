from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# PROPOSALS


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    dao_id = Column(UUID)
    on_chain_id = Column(Integer)
    user_details_id = Column(UUID)
    name = Column(String)
    image_url = Column(String)
    category = Column(String)
    content = Column(String)
    voting_system = Column(String)
    actions = Column(JSON)
    tags = Column(JSON)
    attachments = Column(JSON)
    date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String)
    is_proposal = Column(Boolean)


class Addendum(Base):
    __tablename__ = "proposal_addendums"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    proposal_id = Column(UUID)
    name = Column(String)
    content = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())


class Comment(Base):
    __tablename__ = "proposal_comments"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    proposal_id = Column(UUID)
    user_details_id = Column(UUID)
    comment = Column(String)
    parent = Column(UUID)
    date = Column(DateTime(timezone=True), server_default=func.now())


class ProposalLike(Base):
    __tablename__ = "proposal_likes"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    proposal_id = Column(UUID)
    user_details_id = Column(UUID)
    liked = Column(Boolean)


class ProposalCommentLike(Base):
    __tablename__ = "proposal_comments_likes"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    comment_id = Column(UUID)
    user_details_id = Column(UUID)
    liked = Column(Boolean)


class ProposalFollower(Base):
    __tablename__ = "proposal_followers"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    proposal_id = Column(UUID)
    user_details_id = Column(UUID)


class ProposalReference(Base):
    __tablename__ = "proposal_references"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    referred_proposal_id = Column(UUID)
    referring_proposal_id = Column(UUID)
