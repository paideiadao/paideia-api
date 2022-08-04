from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect
import typing as t
from starlette.responses import JSONResponse

from core.auth import get_current_active_superuser, get_current_active_user

from db.session import get_db
from db.crud.notifications import (
    cleanup_notifications,
    create_notification,
    edit_notification,
    delete_notification,
    get_notifications
)
from db.schemas.notifications import CreateAndUpdateNotification, Notification
from websocket.connection_manager import connection_manager

notification_router = r = APIRouter()


@r.get(
    "/{user_id}",
    response_model=t.List[Notification],
    response_model_exclude_none=True,
    name="notifications:all-notifications"
)
def notifications_list(
    user_id: int,
    db=Depends(get_db),
):
    """
    Get all notifications for a user
    """
    try:
        return get_notifications(db, user_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/{user_id}", response_model=Notification, response_model_exclude_none=True, name="notifications:create")
async def notification_create(
    user_id: int,
    notification: CreateAndUpdateNotification,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new notification
    """
    try:
        ret = create_notification(db, user_id, notification)
        await connection_manager.send_personal_message("notification_user_id_" + str(user_id), {"notifications": get_notifications(db, user_id)})
        return ret
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put("/mark_as_read/{notification_id}", response_model=Notification, response_model_exclude_none=True, name="notifications:read")
def notification_edit(
    notification_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Mark notification as read by user
    """
    try:
        return edit_notification(db, notification_id, current_user.id, CreateAndUpdateNotification(user_id=current_user.id, is_read=True))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/clean_up", name="notifications:clean-up"
)
def notification_cleanup(
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete old notifcations for all users
    """
    try:
        return cleanup_notifications(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{notification_id}", response_model=Notification, response_model_exclude_none=True, name="notifications:delete"
)
def notification_delete(
    notification_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing notification
    """
    try:
        return delete_notification(db, notification_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    key = "notification_user_id_" + user_id
    await connection_manager.connect(key, websocket)
    try:
        while True:
            # pause loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(key)
