import typing as t
import uuid

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from core.auth import get_current_active_superuser
from db.crud.blogs import get_blogs, get_blog, create_blog, edit_blog, delete_blog
from db.schemas.blog import CreateOrUpdateBlog, Blog
from db.session import get_db

blogs_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Blog],
    response_model_exclude_none=True,
    name="blogs:blogs"
)
def blogs_get_all(
    search_string: str = "",
    highlights_only: bool = False,
    education_only: bool = False,
    db=Depends(get_db)
):
    try:
        return get_blogs(db, search_string, highlights_only, education_only)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.get(
    "/{link}",
    response_model=Blog,
    response_model_exclude_none=True,
    name="blogs:get-blog"
)
def blogs_get(
    link,
    db=Depends(get_db)
):
    try:
        return get_blog(db, link)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.post(
    "/",
    response_model=Blog,
    response_model_exclude_none=True,
    name="blogs:create-blog"
)
def blogs_create(
    blog: CreateOrUpdateBlog,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    try:
        return create_blog(db, blog)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.put(
    "/{id}",
    response_model=Blog,
    response_model_exclude_none=True,
    name="blogs:edit-blog"
)
def blogs_edit(
    id: uuid.UUID,
    blog: CreateOrUpdateBlog,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    try:
        return edit_blog(db, id, blog)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))


@r.delete(
    "/{id}",
    response_model=Blog,
    response_model_exclude_none=True,
    name="blogs:delete-blog"
)
def blogs_delete(
    id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    try:
        return delete_blog(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))
