from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
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


def get_user_by_primary_wallet_address(db: Session, primary_wallet_address: str):
    user = db.query(models.User, models.ErgoAddress).filter(models.User.primary_wallet_address_id ==
                                                            models.ErgoAddress.id).filter(models.ErgoAddress.address == primary_wallet_address).first()
    if not user:
        return user
    return user[0]


def get_user_by_wallet_addresses(db: Session, addresses: t.List[str]):
    user = db.query(models.User, models.ErgoAddress).filter(
        models.User.id == models.ErgoAddress.user_id).filter(models.ErgoAddress.address.in_(addresses)).first()
    if not user:
        return user
    return user[0]


def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.UserOut]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    # todo: insert primary wallet address
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        alias=user.alias,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # create empty configs for new user
    db_user_details = models.UserDetails(
        user_id=db_user.id,
        name=db_user.alias,
    )
    db_user_profile_settings = models.UserProfileSettings(
        user_id=db_user.id,
    )
    db.add(db_user_details)
    db.add(db_user_profile_settings)
    db.commit()
    return db_user


def edit_user(
    db: Session, id: int, user: schemas.UserEdit
) -> schemas.User:

    db_user = get_user(db, id)
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


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    db.delete(user)
    db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id).delete()
    db.query(models.UserProfileSettings).filter(
        models.UserProfileSettings.user_id == user_id).delete()
    db.query(models.UserFollower).filter(or_(models.UserFollower.followee_id ==
                                             user_id, models.UserFollower.follower_id == user_id)).delete()
    db.commit()
    return user



def get_followers_by_user_id(db: Session, user_id: int):
    followers = list(map(lambda x: x.follower_id, db.query(
        models.UserFollower).filter(models.UserFollower.followee_id == user_id).all()))
    following = list(map(lambda x: x.followee_id, db.query(
        models.UserFollower).filter(models.UserFollower.follower_id == user_id).all()))
    return {
        "followers": followers,
        "following": following
    }


def get_user_profile(db: Session, user_id: int):
    db_profile = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id).first()
    if not db_profile:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    follower_data = get_followers_by_user_id(db, user_id)
    return schemas.UserDetails(
        id=db_profile.id,
        user_id=db_profile.user_id,
        name=db_profile.name,
        profile_img_url=db_profile.profile_img_url,
        bio=db_profile.bio,
        level=db_profile.level,
        xp=db_profile.xp,
        followers=follower_data["followers"],
        following=follower_data["following"],
        social_links=db_profile.social_links,
    )


def get_user_profile_settings(db: Session, user_id: int):
    db_settings = db.query(models.UserProfileSettings).filter(
        models.UserProfileSettings.user_id == user_id
    ).first()
    if not db_settings:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    return db_settings


def edit_user_profile(db: Session, user_id: int, user_details: schemas.UpdateUserDetails):
    db_profile = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id).first()
    if not db_profile:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")

    update_data = user_details.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return get_user_profile(db, user_id)


def edit_user_profile_settings(db: Session, user_id: int, user_settings: schemas.UpdateUserProfileSettings):
    db_settings = get_user_profile_settings(db, user_id)
    if not db_settings:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    update_data = user_settings.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_settings, key, value)

    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings


def update_user_follower(db: Session, user_id: int, follow_request: schemas.FollowUserRequest):
    if follow_request.type not in ("follow", "unfollow"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Type must by in (follow, unfollow)")
    # delete older entry if exists
    db.query(models.UserFollower).filter(models.UserFollower.followee_id ==
                                         follow_request.user_id).filter(models.UserFollower.follower_id == user_id).delete()
    if follow_request.type == "follow":
        db_follow = models.UserFollower(
            followee_id=follow_request.user_id,
            follower_id=user_id,
        )
        db.add(db_follow)
    db.commit()
    return get_followers_by_user_id(db, user_id)


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
