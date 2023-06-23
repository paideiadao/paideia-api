import uuid
from pydantic import BaseModel
import typing as t
import datetime

class ActionBase(BaseModel):
    actionType: str
    action: dict

class SendFundsActionOutput(BaseModel):
    address: str
    nergs: int
    tokens: t.List[t.List]
    registers: t.List[str]

class SendFundsAction(BaseModel):
    activationTime: int
    optionId: int
    outputs: t.List[SendFundsActionOutput]

class CreateOrUpdateComment(BaseModel):
    user_details_id: int
    comment: t.Optional[str]
    parent: t.Optional[int]


class CreateOrUpdateAddendum(BaseModel):
    name: str
    content: t.Optional[str]


class CreateProposal(BaseModel):
    dao_id: uuid.UUID
    on_chain_id: t.Optional[int]
    user_details_id: uuid.UUID
    name: str
    image_url: t.Optional[str]
    category: t.Optional[str]
    content: t.Optional[str]
    voting_system: t.Optional[str]
    references: t.List[int] = [] # list of proposal ids
    actions: t.Optional[t.List[dict]] = []
    tags: t.Optional[t.List[str]]
    attachments: t.List[str]
    status: t.Optional[str] = "discussion"
    is_proposal: bool = False
    box_height: t.Optional[int]
    votes: t.Optional[t.List[int]]

class CreateOnChainProposal(CreateProposal):
    stake_key: str
    end_time: int
    
class VoteRequest(BaseModel):
    dao_id: uuid.UUID
    stake_key: str
    proposal_id: uuid.UUID
    votes: t.List[int]

class UpdateProposalBasic(CreateProposal):
    pass


class CreateOrUpdateProposal(CreateProposal):
    comments: t.List[CreateOrUpdateComment]
    likes: t.List[int]  # list of user_details_ids who like
    dislikes: t.List[int]  # list of user_details_ids who dislike
    followers: t.List[int]  # list of user_details_ids who follow
    addendums: t.List[CreateOrUpdateAddendum]


class Comment(CreateOrUpdateComment):
    id: uuid.UUID
    proposal_id: uuid.UUID
    date: datetime.datetime
    alias: str
    profile_img_url: t.Optional[str]
    likes: t.List[int]  # list of user_details_ids who like
    dislikes: t.List[int]  # list of user_details_ids who dislike

    class Config:
        orm_mode = True


class Addendum(CreateOrUpdateAddendum):
    id: uuid.UUID
    date: datetime.datetime

    class Config:
        orm_mode = True


class Proposal(CreateOrUpdateProposal):
    id: uuid.UUID
    on_chain_id: t.Optional[int]
    date: datetime.datetime
    comments: t.List[Comment]
    addendums: t.List[Addendum]
    references_meta: t.List
    profile_img_url: t.Optional[str]
    user_followers: t.List[int]
    created: int
    alias: str
    actions: t.Optional[t.List[dict]]
    box_height: t.Optional[int]
    votes: t.Optional[t.List[int]]

    class Config:
        orm_mode = True


class LikeProposalRequest(BaseModel):
    user_details_id: uuid.UUID
    type: str


class FollowProposalRequest(BaseModel):
    user_details_id: uuid.UUID
    type: str


class AddReferenceRequest(BaseModel):
    referred_proposal_id: uuid.UUID


class ProposalReference(BaseModel):
    id: uuid.UUID
    name: str
    likes: t.List[int]
    dislikes: t.List[int]
    img: str
    is_proposal: bool
