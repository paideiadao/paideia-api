import uuid
from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from db.models.users import UserDetails
from db.models import activity_log
from db.schemas import activity

########################################
### CRUD OPERATIONS FOR ACTIVITY LOG ###
########################################


def get_user_activities(db: Session, user_details_id: uuid.UUID, limit: int = 100):
    return (
        db.query(activity_log.vw_activity_log)
        .filter(activity_log.vw_activity_log.user_details_id == user_details_id)
        .order_by(activity_log.vw_activity_log.date.desc())
        .limit(limit)
        .all()
    )


def get_dao_activities(db: Session, dao_id: uuid.UUID, limit: int = 100):
    dao_activities = (
        db.query(activity_log.vw_activity_log, UserDetails)
        .filter(UserDetails.id == activity_log.vw_activity_log.user_details_id)
        .filter(UserDetails.dao_id == dao_id)
        .order_by(activity_log.vw_activity_log.date.desc())
        .limit(limit)
        .all()
    )
    return list(map(lambda x : x[0], dao_activities))


def create_user_activity(
    db: Session, user_details_id: uuid.UUID, activity: activity.CreateOrUpdateActivity
):
    db_activity = activity_log.Activity(
        user_details_id=user_details_id,
        action=activity.action,
        value=activity.value,
        secondary_action=activity.secondary_action,
        secondary_value=activity.secondary_value,
        category=activity.category,
        link=activity.link,
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


def delete_activity(db: Session, id: uuid.UUID):
    activity = (
        db.query(activity_log.Activity).filter(activity_log.Activity.id == id).first()
    )
    if not activity:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="activity not found"
        )
    db.delete(activity)
    db.commit()
    return activity
