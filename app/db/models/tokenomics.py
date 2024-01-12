from sqlalchemy import Boolean, Column, Integer, String, Float
import uuid
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# TOKENOMICS MODEL


class Tokenomics(Base):
    __tablename__ = "tokenomics"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_id = Column(UUID(as_uuid=True))
    type = Column(String)
    token_id = Column(String)
    token_name = Column(String)
    token_ticker = Column(String)
    token_amount = Column(Float)
    token_image_url = Column(String)
    token_remaining = Column(Float)
    token_decimals = Column(Integer)
    is_activated = Column(Boolean)


class TokenHolder(Base):
    __tablename__ = "token_holders"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    ergo_address_id = Column(UUID(as_uuid=True))
    percentage = Column(Float)
    balance = Column(Float)


class TokenomicsTokenHolder(Base):
    __tablename__ = "tokenomics_token_holders"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    token_holder_id = Column(UUID(as_uuid=True))
    tokenomics_id = Column(UUID(as_uuid=True))


class Distribution(Base):
    __tablename__ = "distributions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tokenomics_id = Column(UUID(as_uuid=True))
    distribution_type = Column(String)
    balance = Column(Float)
    percentage = Column(Float)


class DistributionTokenHolder(Base):
    __tablename__ = "distribution_token_holders"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    token_holder_id = Column(UUID(as_uuid=True))
    distribution_id = Column(UUID(as_uuid=True))


class AirdropValidatedField(Base):
    __tablename__ = "airdrop_validated_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    distribution_id = Column(UUID(as_uuid=True))
    value = Column(String)
    number = Column(Integer)


class DistributionConfig(Base):
    __tablename__ = "distribution_config"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    distribution_id = Column(UUID(as_uuid=True))
    property_name = Column(String)
    property_value = Column(String)
    property_data_type = Column(String)
