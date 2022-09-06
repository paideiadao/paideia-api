from sqlalchemy import Boolean, Column, Integer, String, Float

from db.session import Base

# TOKENOMICS MODEL


class Tokenomics(Base):
    __tablename__ = "tokenomics"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(Integer)
    type = Column(String)
    token_id = Column(String)
    token_name = Column(String)
    token_ticker = Column(String)
    token_amount = Column(Float)
    token_image_url = Column(String)
    token_remaining = Column(Float)
    is_activated = Column(Boolean)


class TokenHolder(Base):
    __tablename__ = "token_holders"

    id = Column(Integer, primary_key=True, index=True)
    ergo_address_id = Column(Integer)
    percentage = Column(Float)
    balance = Column(Float)


class TokenomicsTokenHolder(Base):
    __tablename__ = "tokenomics_token_holders"

    id = Column(Integer, primary_key=True, index=True)
    token_holder_id = Column(Integer)
    tokenomics_id = Column(Integer)


class Distribution(Base):
    __tablename__ = "distributions"

    id = Column(Integer, primary_key=True, index=True)
    tokenomics_id = Column(Integer)
    distribution_type = Column(String)
    balance = Column(Float)
    percentage = Column(Float)


class DistributionTokenHolder(Base):
    __tablename__ = "distribution_token_holders"

    id = Column(Integer, primary_key=True, index=True)
    token_holder_id = Column(Integer)
    distribution_id = Column(Integer)


class AirdropValidatedField(Base):
    __tablename__ = "airdrop_validated_fields"

    id = Column(Integer, primary_key=True, index=True)
    distribution_id = Column(Integer)
    value = Column(String)
    number = Column(Integer)


class DistributionConfig(Base):
    __tablename__ = "distribution_config"

    id = Column(Integer, primary_key=True, index=True)
    distribution_id = Column(Integer)
    property_name = Column(String)
    property_value = Column(String)
    property_data_type = Column(String)
