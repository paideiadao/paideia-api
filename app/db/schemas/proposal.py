import uuid
from pydantic import BaseModel
import typing as t
import datetime

from db.schemas.util import SigningRequest

class ConfigValue(BaseModel):
    key: str
    valueType: str
    value: str

class UpdateConfigAction(BaseModel):
    optionId: int
    activationTime: int
    remove: t.List[str]
    update: t.List[ConfigValue]
    insert: t.List[ConfigValue]

class SendFundsActionOutput(BaseModel):
    address: str
    nergs: int
    tokens: t.List[t.List]
    registers: t.List[str]


class SendFundsAction(BaseModel):
    activationTime: int
    optionId: int
    outputs: t.List[SendFundsActionOutput]

class ActionBase(BaseModel):
    actionType: str
    action: t.Union[SendFundsAction, UpdateConfigAction]

class CreateOrUpdateComment(BaseModel):
    user_details_id: uuid.UUID
    comment: t.Optional[str]
    parent: t.Optional[uuid.UUID]


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
    references: t.List[uuid.UUID] = []  # list of proposal ids
    actions: t.Optional[t.List[ActionBase]]
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
    likes: t.List[uuid.UUID]  # list of user_details_ids who like
    dislikes: t.List[uuid.UUID]  # list of user_details_ids who dislike
    followers: t.List[uuid.UUID]  # list of user_details_ids who follow
    addendums: t.List[CreateOrUpdateAddendum]


class Comment(CreateOrUpdateComment):
    id: uuid.UUID
    proposal_id: uuid.UUID
    date: datetime.datetime
    alias: str
    profile_img_url: t.Optional[str]
    likes: t.List[uuid.UUID]  # list of user_details_ids who like
    dislikes: t.List[uuid.UUID]  # list of user_details_ids who dislike

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
    user_followers: t.List[uuid.UUID]
    created: int
    alias: str
    actions: t.Optional[t.List[ActionBase]]
    box_height: t.Optional[int]
    votes: t.Optional[t.List[int]]

    class Config:
        orm_mode = True


class CreateOnChainProposalResponse(SigningRequest):
    proposal: Proposal


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
    likes: t.List[uuid.UUID]
    dislikes: t.List[uuid.UUID]
    img: str
    is_proposal: bool
