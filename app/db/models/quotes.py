from sqlalchemy import Column, Integer, String, Boolean

from db.session import Base

# QUOTE MODEL


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote = Column(String)
    author = Column(String)
    show = Column(Boolean)
