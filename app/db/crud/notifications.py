import datetime
from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import typing as t

from db.models.notifications import Notification
from db.schemas.notifications import Notification as NotificationSchema, CreateAndUpdateNotification


#########################################
### CRUD OPERATIONS FOR NOTIFICATIONS ###
#########################################


def get_notification(db: Session, id: int):
    return db.query(Notification).filter(Notification.id == id).first()


def get_notifications(db: Session, user_details_id: int, skip: int = 0, limit: int = 10):
    return db.query(Notification).filter(
        Notification.user_details_id == user_details_id
    ).order_by(
        Notification.date.desc()
    ).offset(skip).limit(limit).all()


def create_notification(db: Session, user_details_id: int, notification: CreateAndUpdateNotification):
    db_notification = Notification(
        user_details_id=user_details_id,
        img=notification.img,
        action=notification.action,
        proposal_id=notification.proposal_id,
        transaction_id=notification.transaction_id,
        href=notification.href,
        additional_text=notification.additional_text
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def edit_notification(db: Session, id: int, notification: CreateAndUpdateNotification):
    db_notification = get_notification(db, id)
    if not db_notification:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="notification not found")

    update_data = notification.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_notification, key, value)

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def delete_notification(db: Session, id: int):
    notification = db.query(Notification).filter(Notification.id == id).first()
    if not notification:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="notification not found")
    db.delete(notification)
    db.commit()
    return notification


def cleanup_notifications(db: Session):
    # delete month old notifications
    date = datetime.datetime.utcnow() - datetime.timedelta(30)
    ret = {
        "deleted_rows": db.query(Notification).filter(Notification.date <= date).delete()
    }
    db.commit()
    return ret


def generate_action(username: str, action: str):
    return username + ' ' + action
