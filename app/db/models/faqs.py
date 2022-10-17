from sqlalchemy import Column, Integer, String, JSON

from db.session import Base

# FAQ MODEL


class Faq(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(String)
    tags = Column(JSON)
