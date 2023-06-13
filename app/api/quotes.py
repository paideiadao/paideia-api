import typing as t
import uuid

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from db.session import get_db
from db.crud.quotes import (
    get_quotes,
    create_quote,
    delete_quote,
    edit_quote,
)
from db.schemas.quote import CreateAndUpdateQuote, Quote
from core.auth import get_current_active_superuser

quotes_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Quote],
    response_model_exclude_none=True,
    name="quote:all-quotes"
)
def quotes_list(
    show_hidden: bool = False,
    db=Depends(get_db),
):
    """
    Get all quotes
    """
    try:
        return get_quotes(db, show_hidden)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Quote, response_model_exclude_none=True, name="quote:create")
def quote_create(
    quote: CreateAndUpdateQuote,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new quote
    """
    try:
        return create_quote(db, quote)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{quote_id}", response_model=Quote, response_model_exclude_none=True, name="quote:edit"
)
def quote_edit(
    quote_id: uuid.UUID,
    quote: CreateAndUpdateQuote,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing quote
    """
    try:
        return edit_quote(db, quote_id, quote)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{quote_id}", response_model=Quote, response_model_exclude_none=True, name="quote:delete"
)
def quote_delete(
    quote_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing quote
    """
    try:
        return delete_quote(db, quote_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
