import typing as t

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from core.auth import get_current_active_user, get_current_active_superuser
from db.crud.activity_log import (
    get_user_activities,
    create_user_activity,
    delete_activity,
    get_dao_activities,
)
from db.crud.users import get_user_details_by_id
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
    user_details_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get all user activities
    """
    try:
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
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
    dao_id: int,
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
    user_details_id: int,
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
    id: int, db=Depends(get_db), current_user=Depends(get_current_active_superuser)
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
