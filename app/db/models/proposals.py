from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from db.session import Base

# PROPOSALS


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(Integer)
    user_details_id = Column(Integer)
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

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer)
    name = Column(String)
    content = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())


class Comment(Base):
    __tablename__ = "proposal_comments"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer)
    user_details_id = Column(Integer)
    comment = Column(String)
    parent = Column(Integer)
    date = Column(DateTime(timezone=True), server_default=func.now())


class ProposalLike(Base):
    __tablename__ = "proposal_likes"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer)
    user_details_id = Column(Integer)
    liked = Column(Boolean)


class ProposalCommentLike(Base):
    __tablename__ = "proposal_comments_likes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer)
    user_details_id = Column(Integer)
    liked = Column(Boolean)


class ProposalFollower(Base):
    __tablename__ = "proposal_followers"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer)
    user_details_id = Column(Integer)


class ProposalReference(Base):
    __tablename__ = "proposal_references"

    id = Column(Integer, primary_key=True, index=True)
    referred_proposal_id = Column(Integer)
    referring_proposal_id = Column(Integer)
