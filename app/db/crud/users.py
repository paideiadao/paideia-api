from fastapi import status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
import typing as t

from db.models import users as models
from db.schemas import users as schemas
from core.security import get_password_hash


#################################
### CRUD OPERATIONS FOR USERS ###
#################################


def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    return user


def get_user_by_alias(db: Session, alias: str) -> schemas.UserBase:
    return db.query(models.User).filter(models.User.alias == alias).first()


def get_user_by_primary_wallet_address(db: Session, primary_wallet_address):
    return db.query(models.User, models.ErgoAddress).filter(models.User.primary_wallet_address_id == models.ErgoAddress.id).filter(models.ErgoAddress.address == primary_wallet_address).first()


def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.UserOut]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        alias=user.alias,
        primary_wallet_address_id=user.primary_wallet_address_id,
        profile_img_url=user.profile_img_url,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    db.delete(user)
    db.commit()
    return user


def edit_user(
    db: Session, user_id: int, user: schemas.UserEdit
) -> schemas.User:
    db_user = get_user(db, user_id)
    if not db_user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    update_data = user.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(user.password)
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_ergo_addresses_by_user_id(db: Session, user_id: int):
    return db.query(models.ErgoAddress).filter(models.ErgoAddress.user_id == user_id).all()


def set_ergo_addresses_by_user_id(db: Session, user_id: int, addresses: t.List[str]):
    # delete older entries if they exist
    db.query(models.ErgoAddress).filter(
        models.ErgoAddress.user_id == user_id).delete()
    db.commit()
    # add new addresses
    for address in addresses:
        db_ergo_address = models.ErgoAddress(
            user_id=user_id,
            address=address,
            is_smart_contract=False,
        )
        db.add(db_ergo_address)
    db.commit()
    return get_ergo_addresses_by_user_id(db, user_id)


def blacklist_token(db: Session, token: str):
    db_token = models.JWTBlackList(token=token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_blacklisted_token(db: Session, token: str):
    return db.query(models.JWTBlackList).filter(models.JWTBlackList.token == token).first()
