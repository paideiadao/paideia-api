import typing as t
import uuid

from fastapi import status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from db.models import faqs as models
from db.schemas import faq as schemas


#########################################
### CRUD OPERATIONS FOR FAQ SECTION ###
#########################################

def get_faq(db: Session, id: uuid.UUID):
    return db.query(models.Faq).filter(models.Faq.id == id).first()


def get_faqs(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.Faq]:
    return db.query(models.Faq).offset(skip).limit(limit).all()


def create_faq(db: Session, faq: schemas.CreateAndUpdateFaq):
    db_faq = models.Faq(
        question=faq.question,
        answer=faq.answer,
        tags=faq.tags,
    )
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq


def delete_faq(db: Session, id: uuid.UUID):
    faq = get_faq(db, id)
    if not faq:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content="faq not found")
    db.delete(faq)
    db.commit()
    return faq


def edit_faq(
    db: Session, id: uuid.UUID, faq: schemas.CreateAndUpdateFaq
) -> schemas.Faq:
    db_faq = get_faq(db, id)
    if not db_faq:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content="faq not found")

    update_data = faq.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_faq, key, value)

    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq
