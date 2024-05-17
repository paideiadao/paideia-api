import uuid
from pydantic import BaseModel, Field

import datetime
import typing as t

from db.schemas import RestrictedAlphabetStr

class DaoBasic(BaseModel):
    id: uuid.UUID
    dao_key: t.Optional[str]
    config_height: t.Optional[int]
    dao_name: t.Optional[str]
    dao_short_description: t.Optional[str]
    dao_url: str
    is_draft: t.Optional[bool] = True
    is_published: t.Optional[bool] = False
    nav_stage: t.Optional[int]
    is_review: t.Optional[bool] = True
    category: t.Optional[str] = "Default"

    class Config:
        orm_mode = True

class DaoTreasury(BaseModel):
    address: str
    balance: dict


class VwDao(BaseModel):
    id: uuid.UUID
    dao_key: t.Optional[str]
    config_height: t.Optional[int]
    dao_name: str
    dao_url: str
    dao_short_description: t.Optional[str]
    logo_url: t.Optional[str]
    token_id: t.Optional[str]
    token_ticker: t.Optional[str]
    category: t.Optional[str]
    created_dtz: datetime.datetime
    member_count: int = 0
    proposal_count: int = 0

    class Config:
        orm_mode = True


class CreateOrUpdateFooterSocialLinks(BaseModel):
    social_network: t.Optional[str]
    link_url: t.Optional[str]


class FooterSocialLinks(CreateOrUpdateFooterSocialLinks):
    id: uuid.UUID

    class Config:
        orm_mode = True


class CreateOrUpdateDaoDesign(BaseModel):
    theme_id: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
    logo_url: t.Optional[str]
    show_banner: t.Optional[bool]
    banner_url: t.Optional[str]
    show_footer: t.Optional[bool]
    footer_text: t.Optional[str]
    footer_social_links: t.List[CreateOrUpdateFooterSocialLinks] = []


class DaoDesign(CreateOrUpdateDaoDesign):
    id: uuid.UUID
    footer_social_links: t.List[FooterSocialLinks]
    theme_name: str
    primary_color: str
    secondary_color: str
    dark_primary_color: str
    dark_secondary_color: str

    class Config:
        orm_mode = True


class CreateOrUpdateGovernance(BaseModel):
    is_optimistic: t.Optional[bool]
    is_quadratic_voting: t.Optional[bool]
    time_to_challenge__sec: t.Optional[int]
    quorum: t.Optional[int]
    vote_duration__sec: t.Optional[int]
    amount: t.Optional[float]
    currency: t.Optional[str] = "ERG"
    support_needed: t.Optional[int]
    governance_whitelist: t.List[int] = []  # ergo address id


class Governance(CreateOrUpdateGovernance):
    id: uuid.UUID

    class Config:
        orm_mode = True


class CreateOrUpdateTokenHolder(BaseModel):
    ergo_address_id: uuid.UUID
    percentage: t.Optional[float]
    balance: t.Optional[float]


class TokenHolder(CreateOrUpdateTokenHolder):
    id: uuid.UUID

    class Config:
        orm_mode = True


class CreateOrUpdateDistribution(BaseModel):
    distribution_type: str
    balance: t.Optional[float]
    percentage: t.Optional[float]
    # distributions have a highly flexible pattern
    additionalDetails: dict


class Distribution(CreateOrUpdateDistribution):
    id: uuid.UUID

    class Config:
        orm_mode = True


class CreateOrUpdateTokenomics(BaseModel):
    type: str = "token"
    token_id: t.Optional[str]
    token_name: t.Optional[str]
    token_ticker: t.Optional[str]
    token_decimals: t.Optional[int]
    token_amount: t.Optional[float]
    token_image_url: t.Optional[str]
    token_remaining: t.Optional[float]
    is_activated: t.Optional[bool]
    token_holders: t.List[CreateOrUpdateTokenHolder] = []
    distributions: t.List[CreateOrUpdateDistribution] = []


class Tokenomics(CreateOrUpdateTokenomics):
    id: uuid.UUID
    token_holders: t.List[TokenHolder] = []
    distributions: t.List[Distribution] = []


class CreateOrUpdateDao(BaseModel):
    dao_key: t.Optional[str]
    config_height: t.Optional[int]
    dao_name: str
    dao_short_description: t.Optional[str]
    dao_url: RestrictedAlphabetStr = Field(alphabet="QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890")
    governance: CreateOrUpdateGovernance
    tokenomics: CreateOrUpdateTokenomics
    design: CreateOrUpdateDaoDesign
    is_draft: t.Optional[bool]
    is_published: t.Optional[bool]
    nav_stage: t.Optional[int]
    is_review: t.Optional[bool]
    category: t.Optional[str] = "Default"


class Dao(CreateOrUpdateDao):
    id: uuid.UUID
    governance: t.Optional[Governance]
    tokenomics: t.Optional[Tokenomics]
    design: t.Optional[DaoDesign]
    created_dtz: datetime.datetime

    class Config:
        orm_mode = True


class DaoConfigEntry(BaseModel):
    valueType: str
    value: str


class CreateOnChainTokenomicsStakingConfig(BaseModel):
    stake_pool_size: int
    staking_emission_amount: int
    staking_emission_delay: int
    staking_cycle_length: int
    staking_profit_share_pct: int

    class Config:
        orm_mode = True


class CreateOnChainTokenomics(BaseModel):
    token_id: str
    token_name: str
    token_ticker: str
    staking_config: CreateOnChainTokenomicsStakingConfig

    class Config:
        orm_mode = True


class CreateOnChainDaoGovernance(BaseModel):
    governance_type: str = "DEFAULT"
    quorum: int
    threshold: int
    min_proposal_time: int
    participation_weight: int
    pure_participation_weight: int

    class Config:
        orm_mode = True


class CreateOnChainDaoDesign(BaseModel):
    theme: str = "default"
    logo: str
    banner_enabled: bool
    banner: t.Optional[str]
    footer_enabled: bool
    footer: t.Optional[str]

    class Config:
        orm_mode = True


class CreateOnChainDao(BaseModel):
    name: str
    url: str
    description: str
    tokenomics: CreateOnChainTokenomics
    governance: CreateOnChainDaoGovernance
    design: CreateOnChainDaoDesign
    user_addresses: t.List[str]

    class Config:
        orm_mode = True
