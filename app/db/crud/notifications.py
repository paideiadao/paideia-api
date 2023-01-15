import datetime
from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from db.models.notifications import Notification
from db.models.proposals import Proposal
from db.schemas.notifications import (
    Notification as NotificationSchema,
    CreateAndUpdateNotification,
)


#########################################
### CRUD OPERATIONS FOR NOTIFICATIONS ###
#########################################


def get_notification(db: Session, id: int):
    return db.query(Notification).filter(Notification.id == id).first()


def get_notifications(
    db: Session, user_details_id: int, skip: int = 0, limit: int = 10
):
    res = (
        db.query(Notification, Proposal)
        .filter(Notification.proposal_id == Proposal.id)
        .filter(Notification.user_details_id == user_details_id)
        .order_by(Notification.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return list(map(
        lambda x: NotificationSchema(
            user_details_id=x[0].user_details_id,
            img=x[0].img,
            action=x[0].action,
            proposal_id=x[0].proposal_id,
            proposal_name=x[1].name,
            transaction_id=x[0].transaction_id,
            href=x[0].href,
            additional_text=x[0].additional_text,
            is_read=x[0].is_read,
            id=x[0].id,
            date=x[0].date,
        ),
        res
    ))


def create_notification(
    db: Session, user_details_id: int, notification: CreateAndUpdateNotification
):
    db_notification = Notification(
        user_details_id=user_details_id,
        img=notification.img,
        action=notification.action,
        proposal_id=notification.proposal_id,
        transaction_id=notification.transaction_id,
        href=notification.href,
        additional_text=notification.additional_text,
        is_read=False,
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def edit_notification(db: Session, id: int, notification: CreateAndUpdateNotification):
    db_notification = get_notification(db, id)
    if not db_notification:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="notification not found"
        )

    update_data = notification.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_notification, key, value)

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def mark_all_as_read(db: Session, user_details_id: int):
    db_notifications = db.query(Notification).filter(
        Notification.user_details_id == user_details_id
    ).all()
    for db_notification in db_notifications:
        setattr(db_notification, "is_read", True)
        db.add(db_notification)

    db.commit()
    return get_notifications(db, user_details_id)


def delete_notification(db: Session, id: int):
    notification = db.query(Notification).filter(Notification.id == id).first()
    if not notification:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="notification not found"
        )
    db.delete(notification)
    db.commit()
    return notification


def cleanup_notifications(db: Session):
    # delete month old notifications
    date = datetime.datetime.utcnow() - datetime.timedelta(30)
    ret = {
        "deleted_rows": db.query(Notification)
        .filter(Notification.date <= date)
        .delete()
    }
    db.commit()
    return ret


def generate_action(username: str, action: str):
    return username + " " + action
