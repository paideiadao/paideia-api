from sqlalchemy import Boolean, Column, Integer, String, DateTime

from db.session import Base

# DAO DESIGN AND THEME


class DaoDesign(Base):
    __tablename__ = "dao_designs"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(Integer)
    theme_id = Column(Integer)
    logo_url = Column(String)
    show_banner = Column(Boolean)
    banner_url = Column(String)
    show_footer = Column(Boolean)
    footer_text = Column(String)


class DaoTheme(Base):
    __tablename__ = "dao_themes"

    id = Column(Integer, primary_key=True)
    theme_name = Column(String)
    primary_color = Column(String)
    secondary_color = Column(String)
    dark_primary_color = Column(String)
    dark_secondary_color = Column(String)



class FooterSocialLinks(Base):
    __tablename__ = "footer_social_links"

    id = Column(Integer, primary_key=True, index=True)
    design_id = Column(Integer)
    social_network = Column(String)
    link_url = Column(String)
