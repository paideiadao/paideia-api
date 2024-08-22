import requests
import traceback
import logging
import uuid

from sqlalchemy.orm import Session

from api.notifications import notification_create
from core.async_handler import run_coroutine_in_sync
from db.crud.dao import get_dao_by_url
from db.crud.notifications import filter_additional_text_exists
from db.crud.users import get_user_by_wallet_address, get_user_details_from_user
from db.schemas.notifications import CreateAndUpdateNotification, NotificationConstants
from db.session import get_db

from config import Config, Network


CFG = Config[Network]
PLUGIN_NAMES = [
    "PaideiaStakingPlugin",
    "PaideiaVotingPlugin",
    "PaideiaProposalPlugin"
]


def sync_notifications():
    for plugin_name in PLUGIN_NAMES:
        sync_notifications_for_plugin(plugin_name)


def sync_notifications_for_plugin(plugin_name: str):
    try:
        db = next(get_db())
        res = requests.get(CFG.notifications_api + "/sync_events/" + plugin_name)
        resj = res.json()
        for event in resj:
            address = event["address"]
            dao_url = event["body"]["dao"]
            dao_details = get_dao_by_url(db, dao_url)
            if not dao_details:
                logging.error("dao_details not found for dao: " + dao_url)
                # this should never happen
                continue
            dao_id = dao_details.id
            if filter_additional_text_exists(db, get_additional_text(event)):
                logging.info("Ignoring duplicate event: " + event["id"])
                continue
            user_details_id = get_user_details_id(address, dao_id, db)
            if not user_details_id:
                logging.info("Event does not have a coresponding user profile: " + event["id"])
                continue
            notification = CreateAndUpdateNotification(
                    user_details_id=user_details_id,
                    action=get_action_from_event(event),
                    transaction_id=event["transactionId"],
                    additional_text=get_additional_text(event)
                )
            # handle async web sockets stuff
            run_coroutine_in_sync(
                notification_create(
                    user_details_id, notification, db, current_user=None
                )
            )
    except Exception as e:
        logging.error(traceback.format_exc())


def get_user_details_id(address: str, dao_id: uuid.UUID, db: Session):
    user = get_user_by_wallet_address(db, address)
    if not user:
        return user
    user_id = user.id
    user_details = get_user_details_from_user(db, user_id, dao_id)
    if not user_details:
        return user_details
    return user_details.id


def get_action_from_event(event):
    body = event["body"]
    if body["type"] == "add_stake" and body["status"] == "submitted":
        return NotificationConstants.ADD_STAKE_TRANSACTION_SUBMITTED
    if body["type"] == "add_stake" and body["status"] == "confirmed":
        return NotificationConstants.ADD_STAKE_TRANSACTION_CONFIRMED
    if body["type"] == "remove_stake" and body["status"] == "submitted":
        return NotificationConstants.REMOVE_STAKE_TRANSACTION_SUBMITTED
    if body["type"] == "remove_stake" and body["status"] == "confirmed":
        return NotificationConstants.REMOVE_STAKE_TRANSACTION_CONFIRMED
    if body["type"] == "create_proposal" and body["status"] == "submitted":
        return NotificationConstants.CREATE_PROPOSAL_TRANSACTION_SUBMITTED
    if body["type"] == "create_proposal" and body["status"] == "confirmed":
        return NotificationConstants.CREATE_PROPOSAL_TRANSACTION_CONFIRMED
    if body["type"] == "vote" and body["status"] == "submitted":
        return NotificationConstants.VOTE_TRANSACTION_SUBMITTED
    if body["type"] == "vote" and body["status"] == "confirmed":
        return NotificationConstants.VOTE_TRANSACTION_CONFIRMED
    return "default_action"


def get_additional_text(event):
    return "eventId=" + event["id"] + "&" + "timestamp=" + event["timestamp"]
