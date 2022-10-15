## proposals.py (crud)

import typing as t

from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from db.crud.users import (
    get_followers_by_user_id,
    get_proposals_by_user_id,
    get_primary_wallet_address_by_user_id,
    get_user_details_by_id,
)
from db.models.users import UserDetails

from db.models.proposals import (
    Proposal,
    ProposalReference,
    ProposalLike,
    ProposalFollower,
    Comment,
    Addendum,
    ProposalCommentLike,
)
from db.schemas.proposal import (
    ProposalReference as ProposalReferenceSchema,
    Proposal as ProposalSchema,
    CreateProposal as CreateProposalSchema,
    Comment as CommentSchema,
    UpdateProposalBasic as UpdateProposalBasicSchema,
    CreateOrUpdateAddendum,
    CreateOrUpdateComment,
)

#####################################
### CRUD OPERATIONS FOR PROPOSALS ###
#####################################


def get_basic_proposal_by_id(db: Session, id: int):
    return db.query(Proposal).filter(Proposal.id == id).first()


def get_likes_by_proposal_id(db: Session, proposal_id: int):
    db_likes = (
        db.query(ProposalLike).filter(ProposalLike.proposal_id == proposal_id).all()
    )
    likes = list(map(lambda x: x.user_details_id, filter(lambda x: x.liked, db_likes)))
    dislikes = list(
        map(lambda x: x.user_details_id, filter(lambda x: x.liked == False, db_likes))
    )
    return {"proposal_id": proposal_id, "likes": likes, "dislikes": dislikes}


def get_likes_by_comment_id(db: Session, comment_id: int):
    db_likes = db.query(ProposalCommentLike).filter(
        ProposalCommentLike.comment_id == comment_id
    )
    likes = list(map(lambda x: x.user_details_id, filter(lambda x: x.liked, db_likes)))
    dislikes = list(
        map(lambda x: x.user_details_id, filter(lambda x: x.liked == False, db_likes))
    )
    return {"comment_id": comment_id, "likes": likes, "dislikes": dislikes}


def set_likes_by_proposal_id(
    db: Session, proposal_id: int, user_details_id: int, type: str
):
    if type not in ("like", "dislike", "remove"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content="invalid like request type"
        )
    db.query(ProposalLike).filter(ProposalLike.proposal_id == proposal_id).filter(
        ProposalLike.user_details_id == user_details_id
    ).delete()
    if type == "like":
        db_like = ProposalLike(
            proposal_id=proposal_id, user_details_id=user_details_id, liked=True
        )
        db.add(db_like)
    if type == "dislike":
        db_like = ProposalLike(
            proposal_id=proposal_id, user_details_id=user_details_id, liked=False
        )
        db.add(db_like)

    db.commit()
    return get_likes_by_proposal_id(db, proposal_id)


def set_likes_by_comment_id(
    db: Session, comment_id: int, user_details_id: int, type: str
):
    if type not in ("like", "dislike", "remove"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content="invalid like request type"
        )
    db.query(ProposalCommentLike).filter(
        ProposalCommentLike.comment_id == comment_id
    ).filter(ProposalCommentLike.user_details_id == user_details_id).delete()
    if type == "like":
        db_like = ProposalCommentLike(
            comment_id=comment_id, user_details_id=user_details_id, liked=True
        )
        db.add(db_like)
    if type == "dislike":
        db_like = ProposalCommentLike(
            comment_id=comment_id, user_details_id=user_details_id, liked=False
        )
        db.add(db_like)

    db.commit()
    return get_likes_by_comment_id(db, comment_id)


def get_followers_by_proposal_id(db: Session, proposal_id: int):
    db_followers = (
        db.query(ProposalFollower)
        .filter(ProposalFollower.proposal_id == proposal_id)
        .all()
    )
    followers = list(map(lambda x: x.user_details_id, db_followers))
    return {"proposal_id": proposal_id, "followers": followers}


def set_followers_by_proposal_id(
    db: Session, proposal_id: int, user_details_id: int, type: str
):
    if type not in ("follow", "unfollow"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="invalid follow request type",
        )
    db.query(ProposalFollower).filter(
        ProposalFollower.proposal_id == proposal_id
    ).filter(ProposalFollower.user_details_id == user_details_id).delete()
    if type == "follow":
        db_follow = ProposalFollower(
            proposal_id=proposal_id,
            user_details_id=user_details_id,
        )
        db.add(db_follow)

    db.commit()
    return get_followers_by_proposal_id(db, proposal_id)


def get_references_by_proposal_id(db: Session, proposal_id: int):
    db_references = (
        db.query(ProposalReference)
        .filter(ProposalReference.referring_proposal_id == proposal_id)
        .all()
    )
    references = list(map(lambda x: x.referred_proposal_id, db_references))
    references_meta = []
    for reference in references:
        db_proposal: Proposal = (
            db.query(Proposal).filter(Proposal.id == reference).first()
        )
        likes = get_likes_by_proposal_id(db, db_proposal.id)
        references_meta.append(
            ProposalReferenceSchema(
                id=db_proposal.id,
                name=db_proposal.name,
                img=db_proposal.image_url,
                likes=likes["likes"],
                dislikes=likes["dislikes"],
                status=db_proposal.status,
                is_proposal=db_proposal.is_proposal,
            )
        )

    return {
        "proposal_id": proposal_id,
        "references": references,
        "references_meta": references_meta,
    }


def add_reference_by_proposal_id(
    db: Session, user_details_id: int, proposal_id: int, referred_proposal_id: int
):
    db_proposal = get_basic_proposal_by_id(db, proposal_id)
    if not db_proposal or db_proposal.user_details_id != user_details_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
        )
    db_reference = ProposalReference(
        referred_proposal_id=referred_proposal_id, referring_proposal_id=proposal_id
    )
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def get_comments_by_proposal_id(db: Session, proposal_id: int):
    db_comments = (
        db.query(Comment, UserDetails.name, UserDetails.profile_img_url)
        .filter(Comment.proposal_id == proposal_id)
        .join(UserDetails, Comment.user_details_id == UserDetails.id)
        .all()
    )
    comments = []
    for comment in db_comments:
        likes = get_likes_by_comment_id(db, comment[0].id)
        comments.append(
            CommentSchema(
                id=comment[0].id,
                date=comment[0].date,
                user_details_id=comment[0].user_details_id,
                parent=comment[0].parent,
                comment=comment[0].comment,
                profile_img_url=comment[2],
                alias=comment[1],
                likes=likes["likes"],
                dislikes=likes["dislikes"],
            )
        )

    return comments


def get_comment_by_id(db: Session, id: int):
    db_comment = (
        db.query(Comment, UserDetails.name, UserDetails.profile_img_url)
        .filter(Comment.id == id)
        .join(UserDetails, Comment.user_details_id == UserDetails.id)
        .first()
    )
    if not db_comment:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="comment not found"
        )
    likes = get_likes_by_comment_id(db, db_comment[0].id)
    comment = CommentSchema(
        id=db_comment[0].id,
        date=db_comment[0].date,
        user_details_id=db_comment[0].user_details_id,
        profile_img_url=db_comment[2],
        alias=db_comment[1],
        parent=db_comment[0].parent,
        comment=db_comment[0].comment,
        likes=likes["likes"],
        dislikes=likes["dislikes"],
    )
    return comment


def add_commment_by_proposal_id(
    db: Session, proposal_id: int, comment: CreateOrUpdateComment
):
    db_comment = Comment(
        proposal_id=proposal_id,
        user_details_id=comment.user_details_id,
        parent=comment.parent,
        comment=comment.comment,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_addendums_by_proposal_id(db: Session, proposal_id: int):
    db_addendums = db.query(Addendum).filter(Addendum.proposal_id == proposal_id).all()
    return db_addendums


def add_addendum_by_proposal_id(
    db: Session,
    user_details_id: int,
    proposal_id: int,
    addendum: CreateOrUpdateAddendum,
):
    db_proposal = get_basic_proposal_by_id(db, proposal_id)
    if not db_proposal or db_proposal.user_details_id != user_details_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
        )
    db_addendum = Addendum(
        proposal_id=proposal_id, name=addendum.name, content=addendum.content
    )
    db.add(db_addendum)
    db.commit()
    db.refresh(db_addendum)
    return db_addendum


def get_proposal_by_id(db: Session, id: int):
    db_proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not db_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="proposal not found"
        )
    likes = get_likes_by_proposal_id(db, id)
    followers = get_followers_by_proposal_id(db, id)
    references = get_references_by_proposal_id(db, id)
    comments = get_comments_by_proposal_id(db, id)
    addendums = get_addendums_by_proposal_id(db, id)
    tags = db_proposal.tags["tags_list"] if "tags_list" in db_proposal.tags else []
    attachments = (
        db_proposal.attachments["attachments_list"]
        if "attachments_list" in db_proposal.attachments
        else []
    )
    actions = (
        db_proposal.actions["actions_list"]
        if "actions_list" in db_proposal.actions
        else []
    )
    user_details = get_user_details_by_id(db, db_proposal.user_details_id)
    address = get_primary_wallet_address_by_user_id(db, user_details.user_id)
    proposal = ProposalSchema(
        id=db_proposal.id,
        dao_id=db_proposal.dao_id,
        user_details_id=db_proposal.user_details_id,
        name=db_proposal.name,
        image_url=db_proposal.image_url,
        category=db_proposal.category,
        content=db_proposal.content,
        voting_system=db_proposal.voting_system,
        references=references["references"],
        references_meta=references["references_meta"],
        actions=actions,
        comments=comments,
        likes=likes["likes"],
        dislikes=likes["dislikes"],
        followers=followers["followers"],
        tags=tags,
        attachments=attachments,
        addendums=addendums,
        date=db_proposal.date,
        status=db_proposal.status,
        is_proposal=db_proposal.is_proposal,
        profile_img_url=user_details.profile_img_url,
        alias=user_details.name,
        address=address,
        user_followers=get_followers_by_user_id(db, user_details.id)["followers"],
        created=len(get_proposals_by_user_id(db, user_details.id)),
    )
    return proposal


def get_proposals_by_dao_id(db: Session, dao_id: int):
    db_proposals = db.query(Proposal).filter(Proposal.dao_id == dao_id).all()
    proposals = list(map(lambda x: get_proposal_by_id(db, x.id), db_proposals))
    return proposals


def create_new_proposal(db: Session, proposal: CreateProposalSchema):
    db_proposal = Proposal(
        dao_id=proposal.dao_id,
        user_details_id=proposal.user_details_id,
        name=proposal.name,
        image_url=proposal.image_url,
        category=proposal.category,
        content=proposal.content,
        voting_system=proposal.voting_system,
        actions={"actions_list": proposal.actions},
        tags={"tags_list": proposal.tags},
        attachments={"attachments_list": proposal.attachments},
        status=proposal.status,
        is_proposal=proposal.is_proposal,
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    create_proposal_references(db, db_proposal.id, proposal.references)
    return get_proposal_by_id(db, db_proposal.id)


def create_proposal_references(db: Session, id: int, references: t.List[int]):
    for reference in references:
        temp_proposal = get_proposal_by_id(db, reference)
        if type(temp_proposal) != JSONResponse and id != reference:
            proposal_reference = ProposalReference(
                referred_proposal_id=reference, referring_proposal_id=id
            )
            db.add(proposal_reference)
    db.commit()
    return True


def edit_proposal_basic_by_id(
    db: Session, user_details_id: int, id: int, proposal: UpdateProposalBasicSchema
):
    db_proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not db_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="proposal not found"
        )

    # safety check
    if (
        db_proposal.user_details_id != user_details_id
        or proposal.user_details_id != user_details_id
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
        )

    update_data = proposal.dict(exclude_unset=True)

    if "actions" in update_data:
        update_data["actions"] = {"actions_list": proposal.actions}

    if "tags" in update_data:
        update_data["tags"] = {"tags_list": proposal.tags}

    if "attachments" in update_data:
        update_data["attachements"] = {"attachments_list": proposal.attachments}

    for key, value in update_data.items():
        setattr(db_proposal, key, value)

    db.add(db_proposal)
    db.commit()
    return get_proposal_by_id(db, id)


def delete_proposal_by_id(db: Session, id: int):
    proposal = get_proposal_by_id(db, id)
    if not proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="proposal not found"
        )
    # delete stuff
    db.query(ProposalReference).filter(
        or_(
            ProposalReference.referred_proposal_id == id,
            ProposalReference.referring_proposal_id == id,
        )
    ).delete()
    db.query(ProposalFollower).filter(ProposalFollower.proposal_id == id).delete()
    db.query(ProposalLike).filter(ProposalLike.proposal_id == id).delete()
    db.query(Addendum).filter(Addendum.proposal_id == id).delete()
    db.query(Comment).filter(Comment.proposal_id == id).delete()
    db.query(Proposal).filter(Proposal.id == id).delete()
    db.commit()
    return proposal
