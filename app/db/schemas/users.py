import uuid
from pydantic import BaseModel, Field

import typing as t

from db.schemas import RestrictedAlphabetStr


### SCHEMAS FOR USERS ###
# Note: alias by default is the primary wallet address
# except for admin accounts


class UserBase(BaseModel):
    alias: str
    is_active: bool = True
    is_superuser: bool = False


class UserOut(UserBase):
    primary_wallet_address_id: t.Optional[uuid.UUID]


class UserCreate(UserBase):
    primary_wallet_address: t.Optional[str]
    password: str = "__ergoauth_default"

    class Config:
        orm_mode = True


class UserSignUp(BaseModel):
    alias: str
    primary_wallet_address: str


class UserEdit(UserBase):
    password: t.Optional[str]

    class Config:
        orm_mode = True


class User(UserOut):
    id: uuid.UUID

    class Config:
        orm_mode = True


class UserAddressConfig(BaseModel):
    id: uuid.UUID
    alias: str  # primary address for users
    registered_addresses: t.List[str] = []
    access_token: t.Optional[str]


class UpdateUserDetails(BaseModel):
    name: RestrictedAlphabetStr = Field(alphabet="QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890")
    profile_img_url: t.Optional[str]
    bio: t.Optional[str]
    level: int = 0
    xp: int = 0
    social_links: t.List[dict] = []


class UserDetails(UpdateUserDetails):
    id: uuid.UUID
    user_id: uuid.UUID
    dao_id: uuid.UUID
    followers: t.List[uuid.UUID]
    following: t.List[uuid.UUID]
    address: t.Optional[str]
    created: int = 0

    class Config:
        orm_mode = True


class UpdateUserProfileSettings(BaseModel):
    settings: dict


class UserProfileSettings(UpdateUserProfileSettings):
    id: uuid.UUID
    user_details_id: uuid.UUID

    class Config:
        orm_mode = True


class FollowUserRequest(BaseModel):
    current_user_details_id: uuid.UUID  # user_details_id for current user
    user_details_id: uuid.UUID
    type: str


class CreateErgoAddress(BaseModel):
    user_id: uuid.UUID
    address: str
    is_smart_contract: bool


class ErgoAddress(CreateErgoAddress):
    id: uuid.UUID

    class Config:
        orm_mode = True


class PrimaryAddressChangeRequest(BaseModel):
    address: str
