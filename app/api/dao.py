import typing as t
import uuid

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse
from core.auth import get_current_active_user, get_current_active_superuser
from db.crud.dao import (
    create_dao,
    edit_dao,
    get_all_daos,
    get_dao,
    get_dao_by_url,
    delete_dao,
    get_highlighted_projects,
    add_to_highlighted_projects,
    remove_from_highlighted_projects,
)
from db.session import get_db
from db.schemas.dao import CreateOrUpdateDao, CreateOrUpdateDaoDesign, CreateOrUpdateGovernance, CreateOrUpdateTokenomics, Dao, DaoTreasury, VwDao
from paideia_state_client import dao
from ergo import indexed_node_client

dao_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[VwDao],
    response_model_exclude_none=True,
    name="dao:all-dao",
)
def dao_list(
    db=Depends(get_db),
):
    """
    Get all dao
    """
    try:
        db_daos = get_all_daos(db)
        state_daos = dao.get_all_daos()
        for d in state_daos:
            daoExistsInDB = False
            for dbd in db_daos:
                if dbd.dao_key == d:
                    daoExistsInDB = True
            if not daoExistsInDB:
                dao_config = dao.get_dao_config(d)
                create_dao(db, CreateOrUpdateDao(
                    dao_key=d,
                    config_height=state_daos[d][1],
                    dao_name=state_daos[d][0],
                    dao_short_description=dao_config.get("im.paideia.dao.description"),
                    dao_url=state_daos[d][0],
                    governance=CreateOrUpdateGovernance(
                        quorum=int(dao_config.get("im.paideia.dao.quorum", 0)),
                        vote_duration__sec=int(dao_config.get("im.paideia.dao.min.proposal.time",0))/1000
                    ),
                    tokenomics=CreateOrUpdateTokenomics(
                        token_id=dao_config["im.paideia.dao.tokenid"]
                    ),
                    design=CreateOrUpdateDaoDesign(footer_social_links=[]),
                    is_draft=False,
                    is_published=True
                ))
        return get_all_daos(db)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/highlights",
    response_model=t.List[VwDao],
    response_model_exclude_none=True,
    name="dao:highlights-dao",
)
def dao_list_highlights(
    db=Depends(get_db),
):
    """
    Get highlighted dao
    """
    try:
        return get_highlighted_projects(db)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
    
@r.get(
    "/treasury/{dao_id}", response_model=DaoTreasury, response_model_exclude_none=True, name="dao:treasury"
)
def get_treasury(
    dao_id: uuid.UUID,
    db=Depends(get_db)
):
    try:
        db_dao = get_dao(db, dao_id)
        treasury_address = dao.get_dao_treasury(db_dao.dao_key)
        treasury_balance = indexed_node_client.get_balance(treasury_address)
        return DaoTreasury(
            address=treasury_address,
            balance=treasury_balance
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/{query}", response_model=Dao, response_model_exclude_none=True, name="dao:get-dao"
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
        if '-' in query:
            dao = get_dao(db, uuid.UUID(query))
        else:
            dao = get_dao_by_url(db, query)
        if not dao:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return dao
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/", response_model=Dao, response_model_exclude_none=True, name="dao:create")
def dao_create(
    dao: CreateOrUpdateDao,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new dao (draft)
    """
    try:
        return create_dao(db, dao)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put(
    "/{id}", response_model=Dao, response_model_exclude_none=True, name="dao:edit-dao"
)
def dao_edit(
    id: uuid.UUID,
    dao: CreateOrUpdateDao,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    edit existing dao
    """
    try:
        dao = edit_dao(db, id, dao)
        if not dao:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return dao
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/highlight/{id}", name="dao:highlight")
def dao_highlight(
    id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Add dao to highlights
    """
    try:
        return add_to_highlighted_projects(db, id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.delete(
    "/{id}", response_model=Dao, response_model_exclude_none=True, name="dao:delete-dao"
)
def dao_delete(
    id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    delete dao
    """
    try:
        dao = delete_dao(db, id)
        if not dao:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return dao
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.delete("/highlight/{id}", name="dao:remove-highlight")
def delete_highlight(
    id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Remove dao from highlights
    """
    try:
        ret = remove_from_highlighted_projects(db, id)
        if not ret:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return ret
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
