import uuid

from datetime import datetime
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.dao import get_treasury_transactions
from cache.cache import cache
from db.crud.activity_log import get_dao_activities
from db.models.users import UserDetails
from db.models.notifications import Notification


def get_aggregated_activities(db: Session, dao_id: uuid.UUID):
    cached = cache.get("get_aggregated_activities_" + str(dao_id))
    if cached:
        return cached
    db_activities = get_activities_by_dao_id(db, dao_id)
    notification_activites = get_notification_activities_by_dao_id(db, dao_id)
    treasury_activities = get_tresuary_activites_by_dao_id(db, dao_id)
    db_activities.extend(notification_activites)
    db_activities.extend(treasury_activities)
    activities = []
    filter = set()
    for activity in db_activities:
        if generate_hash(activity) in filter:
            continue
        filter.add(generate_hash(activity))
        activities.append(activity)
    activities.sort(key=lambda x: datetime.strptime(
        x["date"].split("+")[0], "%Y-%m-%d %H:%M:%S.%f").timestamp(), reverse=True)
    cache.set("get_aggregated_activities_" + str(dao_id), activities)
    return activities


def get_notification_activities_by_dao_id(db: Session, dao_id: uuid.UUID):
    cached = cache.get("get_notification_activities_by_dao_id_" + str(dao_id))
    if cached:
        return cached
    db_notifications = (
        db.query(Notification, UserDetails)
        .join(UserDetails, Notification.user_details_id == UserDetails.id)
        .filter(UserDetails.dao_id == dao_id)
        .filter(Notification.transaction_id != None)
        .order_by(Notification.date.desc())
        .limit(100)
        .all()
    )
    res = list(filter(lambda x: "confirm" in x["action"], map(
        lambda x: {
            "id": str(x[0].id),
            "name": x[1].name,
            "user_details_id": str(x[0].user_details_id),
            "img_url": x[1].profile_img_url,
            "action": x[0].action,
            "value": x[0].transaction_id,
            "date": str(x[0].date),
            "category": "Transactions",
            "secondary_action": None,
            "secondary_value": None
        },
        db_notifications
    )))
    cache.set("get_notification_activities_by_dao_id_" + str(dao_id), res)
    return res


def get_activities_by_dao_id(db: Session, dao_id: uuid.UUID):
    cached = cache.get("get_activities_by_dao_id_" + str(dao_id))
    if cached:
        return cached
    db_activities = get_dao_activities(db, dao_id)
    res = list(map(
        lambda x: {
            "id": str(x.id),
            "name": x.name,
            "user_details_id": str(x.user_details_id),
            "img_url": x.img_url,
            "action": x.action,
            "value": x.value,
            "date": str(x.date),
            "category": x.category,
            "secondary_action": x.secondary_action,
            "secondary_value": x.secondary_value
        },
        db_activities
    ))
    cache.set("get_activities_by_dao_id_" + str(dao_id), res)
    return res


def get_tresuary_activites_by_dao_id(db: Session, dao_id: uuid.UUID):
    transactions_response = get_treasury_transactions(dao_id, 0, 100, db)
    if type(transactions_response) == JSONResponse:
        return []
    transactions = transactions_response["transactions"]
    return list(map(lambda x:  {
        "id": str(uuid.uuid4()),
        "name": x["label"],
        "user_details_id": str(uuid.uuid4()),
        "action": "transaction was executed with id",
        "value": x["transaction_id"],
        "date": str(datetime.utcfromtimestamp(x["time"] / 1000)) + "+00:00",
        "category": "Transactions",
    }, transactions))


def generate_hash(activity):
    raw_date = activity["date"].split("+")[0]
    date = int(datetime.strptime(
        raw_date, "%Y-%m-%d %H:%M:%S.%f").timestamp()) // 10
    return activity["name"] + activity["user_details_id"] + activity["action"] + activity["value"] + activity["category"] + str(date)
