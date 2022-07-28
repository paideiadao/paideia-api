from ast import Add
import typing as t

from sqlalchemy.orm import Session

from db.models.proposals import Proposal, ProposalReference, ProposalLike, ProposalFollower, Comment, Addendum
from db.schemas.proposal import Proposal as ProposalSchema, CreateProposal as CreateProposalSchema, CreateOrUpdateProposal as CreateOrUpdateProposalSchema

#####################################
### CRUD OPERATIONS FOR PROPOSALS ###
#####################################


def get_likes_by_proposal_id(db: Session, proposal_id: int):
    db_likes = db.query(ProposalLike).filter(
        ProposalLike.proposal_id == proposal_id).all()
    likes = list(map(lambda x: x.user_id, filter(lambda x: x.liked, db_likes)))
    dislikes = list(map(lambda x: x.user_id, filter(
        lambda x: x.liked == False, db_likes)))
    return {
        "proposal_id": proposal_id,
        "likes": likes,
        "dislikes": dislikes
    }


def get_followers_by_proposal_id(db: Session, proposal_id: int):
    db_followers = db.query(ProposalFollower).filter(
        ProposalFollower.proposal_id == proposal_id).all()
    followers = list(map(lambda x: x.user_id, db_followers))
    return {
        "proposal_id": proposal_id,
        "followers": followers
    }


def get_references_by_proposal_id(db: Session, proposal_id: int):
    db_references = db.query(ProposalReference).filter(
        ProposalReference.referred_proposal_id == proposal_id
    ).all()
    references = list(map(lambda x: x.referring_proposal_id, db_references))
    return {
        "proposal_id": proposal_id,
        "references": references
    }


def get_comments_by_proposal_id(db: Session, proposal_id: int):
    db_comments = db.query(Comment).filter(
        Comment.proposal_id == proposal_id).all()
    return db_comments


def get_addendums_by_proposal_id(db: Session, proposal_id: int):
    db_addendums = db.query(Addendum).filter(
        Addendum.proposal_id == proposal_id).all()
    return db_addendums


def get_proposal(db: Session, id: int):
    db_proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not db_proposal:
        return None
    likes = get_likes_by_proposal_id(db, id)
    followers = get_followers_by_proposal_id(db, id)
    references = get_references_by_proposal_id(db, id)
    comments = get_comments_by_proposal_id(db, id)
    tags = db_proposal.tags["tags_list"] if "tags_list" in db_proposal.tags else []
    attachments = db_proposal.attachments["attachments_list"] if "attachments_list" in db_proposal.attachments else []
    actions = db_proposal.actions["actions_list"] if "actions_list" in db_proposal.actions else []
    proposal = ProposalSchema(
        id=db_proposal.id,
        dao_id=db_proposal.dao_id,
        user_id=db_proposal.user_id,
        name=db_proposal.name,
        image_url=db_proposal.image_url,
        category=db_proposal.category,
        content=db_proposal.content,
        voting_system=db_proposal.voting_system,
        references=references["references"],
        actions=actions,
        comments=comments,
        likes=likes["likes"],
        dislikes=likes["dislikes"],
        followers=followers["followers"],
        tags=tags,
        attachments=attachments,
        addendums=[],
        date=db_proposal.date,
        is_proposal=db_proposal.is_proposal
    )
    return proposal


def get_proposals_by_dao_id(db: Session, dao_id: int):
    db_proposals = db.query(Proposal).filter(Proposal.dao_id == dao_id).all()
    proposals = list(map(lambda x: get_proposal(db, x.id), db_proposals))
    return proposals


def create_new_proposal(db: Session, proposal: CreateProposalSchema):
    db_proposal = Proposal(
        dao_id=proposal.dao_id,
        user_id=proposal.user_id,
        name=proposal.name,
        image_url=proposal.image_url,
        category=proposal.category,
        content=proposal.content,
        voting_system=proposal.voting_system,
        actions={"actions_list": proposal.actions},
        tags={"tags_list": proposal.tags},
        attachments={"attachments_list": proposal.attachments},
        is_proposal=proposal.is_proposal
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return get_proposal(db, db_proposal.id)
