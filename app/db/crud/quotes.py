import typing as t

from fastapi import status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from db.models import quotes as models
from db.schemas import quote as schemas


#########################################
### CRUD OPERATIONS FOR QUOTES SECTION ###
#########################################

def get_quote(db: Session, id: int):
    return db.query(models.Quote).filter(models.Quote.id == id).first()


def get_quotes(
    db: Session, show_hidden: bool, skip: int = 0, limit: int = 100
) -> t.List[schemas.Quote]:
    if show_hidden:
        return db.query(models.Quote).offset(skip).limit(limit).all()
    return db.query(models.Quote).filter(
        models.Quote.show == True
    ).offset(skip).limit(limit).all()


def create_quote(db: Session, quote: schemas.CreateAndUpdateQuote):
    db_quote = models.Quote(
        quote=quote.quote,
        author=quote.author,
        show=quote.show
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote


def delete_quote(db: Session, id: int):
    quote = get_quote(db, id)
    if not quote:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content="quote not found")
    db.delete(quote)
    db.commit()
    return quote


def edit_quote(
    db: Session, id: int, quote: schemas.CreateAndUpdateQuote
) -> schemas.Quote:
    db_quote = get_quote(db, id)
    if not db_quote:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content="quote not found")

    update_data = quote.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quote, key, value)

    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote
