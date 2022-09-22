from pydantic import BaseModel
import typing as t


### SCHEMAS FOR USERS ###
# Note: alias by default is the primary wallet address
# except for admin accounts

class UserBase(BaseModel):
    alias: str
    is_active: bool = True
    is_superuser: bool = False


class UserOut(UserBase):
    primary_wallet_address_id: t.Optional[int]


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
    id: int

    class Config:
        orm_mode = True


class UserAddressConfig(BaseModel):
    id: int
    alias: str  # primary address for users
    registered_addresses: t.List[str] = []
    access_token: t.Optional[str]


class UpdateUserDetails(BaseModel):
    name: t.Optional[str]
    profile_img_url: t.Optional[str]
    bio: t.Optional[str]
    level: int = 0
    xp: int = 0
    social_links: t.Optional[t.List[dict]]


class UserDetails(UpdateUserDetails):
    id: int
    user_id: int
    dao_id: int
    followers: t.List[int]
    following: t.List[int]

    class Config:
        orm_mode = True


class UpdateUserProfileSettings(BaseModel):
    settings: dict


class UserProfileSettings(UpdateUserProfileSettings):
    id: int
    user_id: int
    dao_id: int

    class Config:
        orm_mode = True


class FollowUserRequest(BaseModel):
    user_id: int
    type: str


class CreateErgoAddress(BaseModel):
    user_id: int
    address: str
    is_smart_contract: bool


class ErgoAddress(CreateErgoAddress):
    id: int

    class Config:
        orm_mode = True


class PrimaryAddressChangeRequest(BaseModel):
    address: str
