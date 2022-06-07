from pydantic import BaseModel
import typing as t


### SCHEMAS FOR USERS ###


class UserBase(BaseModel):
    alias: str
    primary_wallet_address_id: t.Optional[int]
    profile_img_url: t.Optional[str]
    is_active: bool = True
    is_superuser: bool = False


class UserOut(UserBase):
    pass


class UserCreate(UserBase):
    password: str

    class Config:
        orm_mode = True


class UserEdit(UserBase):
    password: t.Optional[str] = None

    class Config:
        orm_mode = True


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class CreateErgoAddress(BaseModel):
    user_id: int
    address: str
    is_smart_contract: bool


class ErgoAddress(CreateErgoAddress):
    id: int

    class Config:
        orm_mode = True
