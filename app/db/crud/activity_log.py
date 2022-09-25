import datetime
import typing as t

from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from db.models import activity_log
from db.schemas import activity

########################################
### CRUD OPERATIONS FOR ACTIVITY LOG ###
########################################


def get_user_activities(db: Session, user_details_id: int):
    return db.query(activity_log.Activity).filter(
        activity_log.Activity.user_details_id == user_details_id
    ).all()


def create_user_activity(db: Session, user_details_id: int, activity: activity.CreateOrUpdateActivity):
    db_activity = activity_log.Activity(
        user_details_id=user_details_id,
        img_url=activity.img_url,
        action=activity.action,
        value=activity.value,
        secondary_action=activity.secondary_action,
        secondary_value=activity.secondary_value,
        category=activity.category
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


def delete_activity(db: Session, id: int):
    activity = db.query(activity_log.Activity).filter(
        activity_log.Activity.id == id).first()
    if not activity:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="activity not found")
    db.delete(activity)
    db.commit()
    return activity
