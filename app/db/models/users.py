from sqlalchemy import JSON, Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.session import Base

# USER MODEL


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String, unique=True, index=True, nullable=False)
    primary_wallet_address_id = Column(Integer)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class UserDetails(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    dao_id = Column(Integer)
    name = Column(String)
    profile_img_url = Column(String)
    bio = Column(String)
    level = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    social_links = Column(JSON)


class UserFollower(Base):
    __tablename__ = "user_followers"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer)
    followee_id = Column(Integer)


class UserProfileSettings(Base):
    __tablename__ = "user_profile_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    dao_id = Column(Integer)
    settings = Column(JSON)


class ErgoAddress(Base):
    __tablename__ = "ergo_addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    address = Column(String)
    is_smart_contract = Column(Boolean)


class JWTBlackList(Base):
    __tablename__ = "jwt_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
