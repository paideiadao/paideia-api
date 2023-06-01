import uuid
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

# DAO DESIGN AND THEME


class DaoDesign(Base):
    __tablename__ = "dao_designs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    dao_id = Column(UUID(as_uuid=True))
    theme_id = Column(UUID(as_uuid=True))
    logo_url = Column(String)
    show_banner = Column(Boolean)
    banner_url = Column(String)
    show_footer = Column(Boolean)
    footer_text = Column(String)


class DaoTheme(Base):
    __tablename__ = "dao_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    theme_name = Column(String)
    primary_color = Column(String)
    secondary_color = Column(String)
    dark_primary_color = Column(String)
    dark_secondary_color = Column(String)



class FooterSocialLinks(Base):
    __tablename__ = "footer_social_links"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    design_id = Column(UUID(as_uuid=True))
    social_network = Column(String)
    link_url = Column(String)
