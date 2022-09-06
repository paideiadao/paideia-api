import typing as t

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse
from core.auth import get_current_active_user
from db.crud.dao import create_dao, edit_dao, get_all_daos, get_dao, get_dao_by_url, delete_dao
from db.session import get_db

from db.schemas.dao import CreateOrUpdateDao, Dao, DaoBasic

dao_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[DaoBasic],
    response_model_exclude_none=True,
    name="dao:all-dao"
)
def dao_list(
    db=Depends(get_db),
):
    """
    Get all dao
    """
    try:
        return get_all_daos(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/{query}",
    response_model=Dao,
    response_model_exclude_none=True,
    name="dao:get-dao"
)
def dao_get(
    query: str,
    db=Depends(get_db),
):
    """
    Get dao
    """
    try:
        dao = None
        if query.isnumeric():
            dao = get_dao(db, int(query))
        else:
            dao = get_dao_by_url(db, query)
        if not dao:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="dao not found")
        return dao
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Dao, response_model_exclude_none=True, name="dao:create")
def dao_create(
    dao: CreateOrUpdateDao,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new dao (draft)
    """
    try:
        return create_dao(db, dao)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{id}",
    response_model=Dao,
    response_model_exclude_none=True,
    name="dao:edit-dao"
)
def dao_edit(
    id: int,
    dao: CreateOrUpdateDao,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    edit existing dao
    """
    try:
        dao = edit_dao(db, id, dao)
        if not dao:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="dao not found")
        return dao
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{id}",
    response_model=Dao,
    response_model_exclude_none=True,
    name="dao:delete-dao"
)
def dao_delete(
    id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    delete dao
    """
    try:
        dao = delete_dao(db, id)
        if not dao:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="dao not found")
        return dao
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
