import typing as t
import uuid

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from core.auth import get_current_active_user, get_current_active_superuser
from db.crud.activity_log import (
    get_user_activities,
    create_user_activity,
    delete_activity,
    get_dao_activities,
)
from db.session import get_db
from db.schemas.activity import Activity, CreateOrUpdateActivity, vwActivity


activity_router = r = APIRouter()


@r.get(
    "/{user_details_id}",
    response_model=t.List[vwActivity],
    response_model_exclude_none=True,
    name="activities:all-user-activities",
)
def activity_list(
    user_details_id: uuid.UUID,
    db=Depends(get_db),
):
    """
    Get all user activities
    """
    try:
        return get_user_activities(db, user_details_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/by_dao_id/{dao_id}",
    response_model=t.List[vwActivity],
    response_model_exclude_none=True,
    name="activities:all-user-activities",
)
def activity_list(
    dao_id: uuid.UUID,
    db=Depends(get_db),
):
    """
    Get all user activities
    """
    try:
        return get_dao_activities(db, dao_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post(
    "/{user_details_id}",
    response_model=Activity,
    response_model_exclude_none=True,
    name="activities:create-activity",
)
def activity_create(
    user_details_id: uuid.UUID,
    activity: CreateOrUpdateActivity,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create user activity
    """
    try:
        return create_user_activity(db, user_details_id, activity)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.delete(
    "/{id}",
    response_model=Activity,
    response_model_exclude_none=True,
    name="activities:delete-activity",
)
def activity_delete(
    id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_active_superuser)
):
    """
    delete user activity
    """
    try:
        return delete_activity(db, id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
