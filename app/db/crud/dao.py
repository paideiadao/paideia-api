import typing as t

from sqlalchemy.orm import Session
from db.models.tokenomics import (
    Distribution,
    TokenHolder,
    Tokenomics,
    TokenomicsTokenHolder,
)
from db.models.dao import Dao, vw_daos
from db.models.dao_design import DaoDesign, FooterSocialLinks
from db.models.governance import Governance, GovernanceWhitelist
from db.schemas.dao import (
    CreateOrUpdateDao,
    CreateOrUpdateDaoDesign,
    CreateOrUpdateDistribution,
    CreateOrUpdateFooterSocialLinks,
    CreateOrUpdateGovernance,
    CreateOrUpdateTokenHolder,
    CreateOrUpdateTokenomics,
    DaoDesign as DaoDesignSchema,
    Governance as GovernanceSchema,
    Dao as DaoSchema,
    Tokenomics as TokenomicsSchema,
    TokenHolder as TokenHolderSchema,
    Distribution as DistributionSchema,
)


################################
### CRUD OPERATIONS FOR DAOS ###
################################


def get_dao_governance_whitelist(db: Session, dao_governance_id: int):
    return list(
        map(
            lambda x: x.ergo_address_id,
            db.query(GovernanceWhitelist)
            .filter(GovernanceWhitelist.governance_id == dao_governance_id)
            .all(),
        )
    )


def set_dao_governance_whitelist(
    db: Session, dao_governance_id: int, whitelist: t.List[int]
):
    # delete older entries if they exist
    db.query(GovernanceWhitelist).filter(
        GovernanceWhitelist.governance_id == dao_governance_id
    ).delete()
    db.commit()
    # add new users
    for ergo_address_id in whitelist:
        db_governance_whitelist = GovernanceWhitelist(
            governance_id=dao_governance_id, ergo_address_id=ergo_address_id
        )
        db.add(db_governance_whitelist)
    db.commit()
    return list(
        map(
            lambda x: x.ergo_address_id,
            db.query(GovernanceWhitelist)
            .filter(GovernanceWhitelist.governance_id == dao_governance_id)
            .all(),
        )
    )


def get_dao_governance(db: Session, dao_id: int):
    db_dao_governance = db.query(Governance).filter(Governance.dao_id == dao_id).first()
    if not db_dao_governance:
        return None

    governance_whitelist = get_dao_governance_whitelist(db, db_dao_governance.id)
    return GovernanceSchema(
        id=db_dao_governance.id,
        is_optimistic=db_dao_governance.is_optimistic,
        is_quadratic_voting=db_dao_governance.is_quadratic_voting,
        time_to_challenge__sec=db_dao_governance.time_to_challenge__sec,
        quorum=db_dao_governance.quorum,
        vote_duration__sec=db_dao_governance.vote_duration__sec,
        amount=db_dao_governance.amount,
        currency=db_dao_governance.currency,
        support_needed=db_dao_governance.support_needed,
        governance_whitelist=governance_whitelist,
    )


def create_dao_governance(
    db: Session, dao_id: int, dao_governance: CreateOrUpdateGovernance
):
    db_dao_governance = Governance(
        dao_id=dao_id,
        is_optimistic=dao_governance.is_optimistic,
        is_quadratic_voting=dao_governance.is_quadratic_voting,
        time_to_challenge__sec=dao_governance.time_to_challenge__sec,
        quorum=dao_governance.quorum,
        vote_duration__sec=dao_governance.vote_duration__sec,
        amount=dao_governance.amount,
        currency=dao_governance.currency,
        support_needed=dao_governance.support_needed,
    )
    db.add(db_dao_governance)
    db.commit()
    db.refresh(db_dao_governance)

    governance_whitelist = set_dao_governance_whitelist(
        db, db_dao_governance.id, dao_governance.governance_whitelist
    )

    return GovernanceSchema(
        id=db_dao_governance.id,
        is_optimistic=dao_governance.is_optimistic,
        is_quadratic_voting=dao_governance.is_quadratic_voting,
        time_to_challenge__sec=dao_governance.time_to_challenge__sec,
        quorum=dao_governance.quorum,
        vote_duration__sec=dao_governance.vote_duration__sec,
        amount=dao_governance.amount,
        currency=dao_governance.currency,
        support_needed=dao_governance.support_needed,
        governance_whitelist=governance_whitelist,
    )


def edit_dao_governance(
    db: Session, dao_id: int, dao_governance: CreateOrUpdateGovernance
):
    db_dao_governance = db.query(Governance).filter(Governance.dao_id == dao_id).first()
    if not db_dao_governance:
        return create_dao_governance(db, dao_id, dao_governance)

    update_data = dao_governance.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("governance_whitelist",):
            continue
        setattr(db_dao_governance, key, value)

    db.add(db_dao_governance)
    db.commit()
    db.refresh(db_dao_governance)

    governance_whitelist = set_dao_governance_whitelist(
        db, db_dao_governance.id, dao_governance.governance_whitelist
    )

    return GovernanceSchema(
        id=db_dao_governance.id,
        is_optimistic=db_dao_governance.is_optimistic,
        is_quadratic_voting=db_dao_governance.is_quadratic_voting,
        time_to_challenge__sec=db_dao_governance.time_to_challenge__sec,
        quorum=db_dao_governance.quorum,
        vote_duration__sec=db_dao_governance.vote_duration__sec,
        amount=db_dao_governance.amount,
        currency=db_dao_governance.currency,
        support_needed=db_dao_governance.support_needed,
        governance_whitelist=governance_whitelist,
    )


def delete_dao_governance(db: Session, dao_id: int):
    db_dao_governance = db.query(Governance).filter(Governance.dao_id == dao_id).first()
    if not db_dao_governance:
        return None

    # delete
    set_dao_governance_whitelist(db, db_dao_governance.id, [])
    db.query(Governance).filter(Governance.dao_id == dao_id).delete()
    db.commit()

    return True


def get_dao_tokenomics_tokenholders(db: Session, dao_tokenomics_id: int):
    return list(
        map(
            lambda x: TokenHolderSchema(
                id=x[0].id,
                ergo_address_id=x[0].ergo_address_id,
                percentage=x[0].percentage,
                balance=x[0].balance,
            ),
            db.query(TokenHolder, TokenomicsTokenHolder)
            .filter(TokenHolder.id == TokenomicsTokenHolder.token_holder_id)
            .filter(TokenomicsTokenHolder.tokenomics_id == dao_tokenomics_id)
            .all(),
        )
    )


def set_dao_tokenomics_tokenholders(
    db: Session, dao_tokenomics_id: int, tokenholders: t.List[CreateOrUpdateTokenHolder]
):
    # delete old entires
    old_tokenholders = (
        db.query(TokenomicsTokenHolder)
        .filter(TokenomicsTokenHolder.tokenomics_id == dao_tokenomics_id)
        .all()
    )
    for tokenholder in old_tokenholders:
        db.query(TokenHolder).filter(
            TokenHolder.id == tokenholder.token_holder_id
        ).delete()
    db.query(TokenomicsTokenHolder).filter(
        TokenomicsTokenHolder.tokenomics_id == dao_tokenomics_id
    ).delete()
    db.commit()

    for tokenholder in tokenholders:
        db_tokenholder = TokenHolder(
            ergo_address_id=tokenholder.ergo_address_id,
            percentage=tokenholder.percentage,
            balance=tokenholder.balance,
        )
        db.add(db_tokenholder)
        db.commit()
        db.refresh(db_tokenholder)
        db_tokenomics_token_holder = TokenomicsTokenHolder(
            token_holder_id=db_tokenholder.id,
            tokenomics_id=dao_tokenomics_id,
        )
        db.add(db_tokenomics_token_holder)
        db.commit()

    return list(
        map(
            lambda x: TokenHolderSchema(
                id=x[0].id,
                ergo_address_id=x[0].ergo_address_id,
                percentage=x[0].percentage,
                balance=x[0].balance,
            ),
            db.query(TokenHolder, TokenomicsTokenHolder)
            .filter(TokenHolder.id == TokenomicsTokenHolder.token_holder_id)
            .filter(TokenomicsTokenHolder.tokenomics_id == dao_tokenomics_id)
            .all(),
        )
    )


def get_dao_tokenomics_distributions(db: Session, dao_tokenomics_id: int):
    return list(
        map(
            lambda x: DistributionSchema(
                id=x.id,
                distribution_type=x.distribution_type,
                balance=x.balance,
                percentage=x.percentage,
                additionalDetails={},
            ),
            db.query(Distribution)
            .filter(Distribution.tokenomics_id == dao_tokenomics_id)
            .all(),
        )
    )


def set_dao_tokenomics_distributions(
    db: Session,
    dao_tokenomics_id: int,
    distributions: t.List[CreateOrUpdateDistribution],
):
    # delete older entries if they exist
    db.query(Distribution).filter(
        Distribution.tokenomics_id == dao_tokenomics_id
    ).delete()
    db.commit()
    # add new users
    for distribution in distributions:
        db_distribution = Distribution(
            tokenomics_id=dao_tokenomics_id,
            distribution_type=distribution.distribution_type,
            balance=distribution.balance,
            percentage=distribution.percentage,
        )
        db.add(db_distribution)
    db.commit()
    return list(
        map(
            lambda x: DistributionSchema(
                id=x.id,
                distribution_type=x.distribution_type,
                balance=x.balance,
                percentage=x.percentage,
                additionalDetails={},
            ),
            db.query(Distribution)
            .filter(Distribution.tokenomics_id == dao_tokenomics_id)
            .all(),
        )
    )


def get_dao_tokenomics(db: Session, dao_id: int):
    db_tokenomics = db.query(Tokenomics).filter(Tokenomics.dao_id == dao_id).first()
    if not db_tokenomics:
        return None

    token_holders = get_dao_tokenomics_tokenholders(db, db_tokenomics.id)
    distributions = get_dao_tokenomics_distributions(db, db_tokenomics.id)

    return TokenomicsSchema(
        id=db_tokenomics.id,
        type=db_tokenomics.type,
        token_id=db_tokenomics.token_id,
        token_name=db_tokenomics.token_name,
        token_ticker=db_tokenomics.token_ticker,
        token_amount=db_tokenomics.token_amount,
        token_image_url=db_tokenomics.token_image_url,
        token_remaining=db_tokenomics.token_remaining,
        is_activated=db_tokenomics.is_activated,
        token_holders=token_holders,
        distributions=distributions,
    )


def create_dao_tokenomics(
    db: Session, dao_id: int, tokenomics: CreateOrUpdateTokenomics
):
    db_dao_tokenomics = Tokenomics(
        dao_id=dao_id,
        type=tokenomics.type,
        token_id=tokenomics.token_id,
        token_name=tokenomics.token_name,
        token_ticker=tokenomics.token_ticker,
        token_amount=tokenomics.token_amount,
        token_image_url=tokenomics.token_image_url,
        token_remaining=tokenomics.token_remaining,
        is_activated=tokenomics.is_activated,
    )

    db.add(db_dao_tokenomics)
    db.commit()
    db.refresh(db_dao_tokenomics)

    token_holders = set_dao_tokenomics_tokenholders(
        db, db_dao_tokenomics.id, tokenomics.token_holders
    )
    distributions = set_dao_tokenomics_distributions(
        db, db_dao_tokenomics.id, tokenomics.distributions
    )

    return TokenomicsSchema(
        id=db_dao_tokenomics.id,
        type=tokenomics.type,
        token_id=tokenomics.token_id,
        token_name=tokenomics.token_name,
        token_ticker=tokenomics.token_ticker,
        token_amount=tokenomics.token_amount,
        token_image_url=tokenomics.token_image_url,
        token_remaining=tokenomics.token_remaining,
        is_activated=tokenomics.is_activated,
        token_holders=token_holders,
        distributions=distributions,
    )


def edit_dao_tokenomics(db: Session, dao_id: int, tokenomics: CreateOrUpdateTokenomics):
    db_tokenomics = db.query(Tokenomics).filter(Tokenomics.dao_id == dao_id).first()
    if not db_tokenomics:
        return create_dao_tokenomics(db, dao_id, tokenomics)

    update_data = tokenomics.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("token_holders", "distributions"):
            continue
        setattr(db_tokenomics, key, value)

    db.add(db_tokenomics)
    db.commit()
    db.refresh(db_tokenomics)

    token_holders = set_dao_tokenomics_tokenholders(
        db, db_tokenomics.id, tokenomics.token_holders
    )
    distributions = set_dao_tokenomics_distributions(
        db, db_tokenomics.id, tokenomics.distributions
    )

    return TokenomicsSchema(
        id=db_tokenomics.id,
        type=db_tokenomics.type,
        token_id=db_tokenomics.token_id,
        token_name=db_tokenomics.token_name,
        token_ticker=db_tokenomics.token_ticker,
        token_amount=db_tokenomics.token_amount,
        token_image_url=db_tokenomics.token_image_url,
        token_remaining=db_tokenomics.token_remaining,
        is_activated=db_tokenomics.is_activated,
        token_holders=token_holders,
        distributions=distributions,
    )


def delete_dao_tokenomics(db: Session, dao_id: int):
    db_tokenomics = db.query(Tokenomics).filter(Tokenomics.dao_id == dao_id).first()
    if not db_tokenomics:
        return None

    # delete
    set_dao_tokenomics_tokenholders(db, db_tokenomics.id, [])
    set_dao_tokenomics_distributions(db, db_tokenomics.id, [])
    db.query(Tokenomics).filter(Tokenomics.dao_id == dao_id).delete()
    db.commit()

    return True


def get_dao_design_footer_links(db: Session, dao_design_id: int):
    return (
        db.query(FooterSocialLinks)
        .filter(FooterSocialLinks.design_id == dao_design_id)
        .all()
    )


def set_dao_design_footer_links(
    db: Session,
    dao_design_id: int,
    footer_links: t.List[CreateOrUpdateFooterSocialLinks],
):
    # delete older entries if they exist
    db.query(FooterSocialLinks).filter(
        FooterSocialLinks.design_id == dao_design_id
    ).delete()
    db.commit()
    # add new links
    for social_link in footer_links:
        db_footer_link = FooterSocialLinks(
            design_id=dao_design_id,
            social_network=social_link.social_network,
            link_url=social_link.link_url,
        )
        db.add(db_footer_link)
    db.commit()
    return (
        db.query(FooterSocialLinks)
        .filter(FooterSocialLinks.design_id == dao_design_id)
        .all()
    )


def get_dao_design(db: Session, dao_id: int):
    db_dao_design = db.query(DaoDesign).filter(DaoDesign.dao_id == dao_id).first()
    if not db_dao_design:
        return None

    footer_links = get_dao_design_footer_links(db, db_dao_design.id)

    return DaoDesignSchema(
        id=db_dao_design.id,
        theme_id=db_dao_design.theme_id,
        logo_url=db_dao_design.logo_url,
        show_banner=db_dao_design.show_banner,
        banner_url=db_dao_design.banner_url,
        show_footer=db_dao_design.show_footer,
        footer_text=db_dao_design.footer_text,
        footer_social_links=footer_links,
    )


def create_dao_design(db: Session, dao_id: int, dao_design: CreateOrUpdateDaoDesign):
    db_dao_design = DaoDesign(
        dao_id=dao_id,
        theme_id=dao_design.theme_id,
        logo_url=dao_design.logo_url,
        show_banner=dao_design.show_banner,
        banner_url=dao_design.banner_url,
        show_footer=dao_design.show_footer,
        footer_text=dao_design.footer_text,
    )
    db.add(db_dao_design)
    db.commit()
    db.refresh(db_dao_design)

    footer_links = set_dao_design_footer_links(
        db, db_dao_design.id, dao_design.footer_social_links
    )

    return DaoDesignSchema(
        id=db_dao_design.id,
        theme_id=dao_design.theme_id,
        logo_url=dao_design.logo_url,
        show_banner=dao_design.show_banner,
        banner_url=dao_design.banner_url,
        show_footer=dao_design.show_footer,
        footer_text=dao_design.footer_text,
        footer_social_links=footer_links,
    )


def edit_dao_design(db: Session, dao_id: int, dao_design: CreateOrUpdateDaoDesign):
    db_dao_design = db.query(DaoDesign).filter(DaoDesign.dao_id == dao_id).first()
    if not db_dao_design:
        return create_dao_design(db, dao_id, dao_design)

    update_data = dao_design.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("footer_social_links",):
            continue
        setattr(db_dao_design, key, value)

    db.add(db_dao_design)
    db.commit()
    db.refresh(db_dao_design)

    footer_links = set_dao_design_footer_links(
        db, db_dao_design.id, dao_design.footer_social_links
    )

    return DaoDesignSchema(
        id=db_dao_design.id,
        theme_id=db_dao_design.theme_id,
        logo_url=db_dao_design.logo_url,
        show_banner=db_dao_design.show_banner,
        banner_url=db_dao_design.banner_url,
        show_footer=db_dao_design.show_footer,
        footer_text=db_dao_design.footer_text,
        footer_social_links=footer_links,
    )


def delete_dao_design(db: Session, dao_id: int):
    db_dao_design = db.query(DaoDesign).filter(DaoDesign.dao_id == dao_id).first()
    if not db_dao_design:
        return None

    # delete
    set_dao_design_footer_links(db, db_dao_design.id, [])
    db.query(DaoDesign).filter(DaoDesign.dao_id == dao_id).delete()
    db.commit()

    return True


def get_all_daos(db: Session):
    return db.query(vw_daos).all()


def get_dao(db: Session, id: int):
    db_dao = db.query(Dao).filter(Dao.id == id).first()
    if not db_dao:
        return None

    dao_design = get_dao_design(db, id)
    dao_governance = get_dao_governance(db, id)
    dao_tokenomics = get_dao_tokenomics(db, id)

    return DaoSchema(
        id=db_dao.id,
        dao_name=db_dao.dao_name,
        dao_short_description=db_dao.dao_short_description,
        dao_url=db_dao.dao_url,
        design=dao_design,
        governance=dao_governance,
        tokenomics=dao_tokenomics,
        is_draft=db_dao.is_draft,
        is_published=db_dao.is_published,
        nav_stage=db_dao.nav_stage,
        is_review=db_dao.is_review,
    )


def get_dao_by_url(db: Session, name: str):
    # preliminary filter
    if name in ("dao",):
        return None

    dao_list = list(
        filter(
            lambda x: (len(x.dao_url.split("/")) != 0)
            and (x.dao_url.split("/")[-1] == name),
            get_all_daos(db),
        )
    )
    if len(dao_list) == 0:
        return None

    dao_id = dao_list[0].id
    return get_dao(db, dao_id)


def create_dao(db: Session, dao: CreateOrUpdateDao):
    db_dao = Dao(
        dao_name=dao.dao_name,
        dao_short_description=dao.dao_short_description,
        dao_url=dao.dao_url,
        is_draft=dao.is_draft,
        is_published=dao.is_published,
        nav_stage=dao.nav_stage,
        is_review=dao.is_review,
    )
    # make the entry for the dao
    # we need to add the tokenomics, design and governance id later
    db.add(db_dao)
    db.commit()
    db.refresh(db_dao)

    dao_id = db_dao.id
    # update design details
    dao_design = create_dao_design(db, dao_id, dao.design)
    dao_governance = create_dao_governance(db, dao_id, dao.governance)
    dao_tokenomics = create_dao_tokenomics(db, dao_id, dao.tokenomics)

    # reverse ids
    setattr(db_dao, "design_id", dao_design.id)
    setattr(db_dao, "tokenomics_id", dao_governance.id)
    setattr(db_dao, "governance_id", dao_tokenomics.id)
    db.add(db_dao)
    db.commit()

    return DaoSchema(
        id=dao_id,
        dao_name=dao.dao_name,
        dao_short_description=dao.dao_short_description,
        dao_url=dao.dao_url,
        design=dao_design,
        governance=dao_governance,
        tokenomics=dao_tokenomics,
        is_draft=dao.is_draft,
        is_published=dao.is_published,
        nav_stage=dao.nav_stage,
        is_review=dao.is_review,
    )


def edit_dao(db: Session, id: int, dao: CreateOrUpdateDao):
    db_dao = db.query(Dao).filter(Dao.id == id).first()
    if not db_dao:
        return None

    update_data = dao.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("design", "governance", "tokenomics"):
            continue
        setattr(db_dao, key, value)

    db.add(db_dao)
    db.commit()
    db.refresh(db_dao)

    dao_design = edit_dao_design(db, id, dao.design)
    dao_governance = edit_dao_governance(db, id, dao.governance)
    dao_tokenomics = edit_dao_tokenomics(db, id, dao.tokenomics)

    return DaoSchema(
        id=db_dao.id,
        dao_name=db_dao.dao_name,
        dao_short_description=db_dao.dao_short_description,
        dao_url=db_dao.dao_url,
        design=dao_design,
        governance=dao_governance,
        tokenomics=dao_tokenomics,
        is_draft=db_dao.is_draft,
        is_published=db_dao.is_published,
        nav_stage=db_dao.nav_stage,
        is_review=db_dao.is_review,
    )


def delete_dao(db: Session, id: int):
    db_dao = db.query(Dao).filter(Dao.id == id).first()
    if not db_dao:
        return None

    db_dao = db_dao.__dict__
    delete_dao_design(db, id)
    delete_dao_governance(db, id)
    delete_dao_tokenomics(db, id)
    db.query(Dao).filter(Dao.id == id).delete()
    db.commit()

    return db_dao
