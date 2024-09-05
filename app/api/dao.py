from dataclasses import Field
import traceback
import logging
import typing as t
import uuid
import urllib

from db.schemas import RestrictedAlphabetStr
from cache.cache import cache
from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse
from paideia_state_client import util
from db.schemas.util import SigningRequest, TokenAmount, Transaction, TransactionHistory
from core.auth import get_current_active_superuser
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
from db.crud.users import create_user_dao_profile
from db.session import get_db
from db.schemas.dao import (
    CreateOrUpdateDao,
    CreateOrUpdateDaoDesign,
    CreateOrUpdateGovernance,
    CreateOrUpdateTokenomics,
    Dao,
    DaoConfigEntry,
    DaoTreasury,
    VwDao,
    CreateOnChainDao,
)
from paideia_state_client import dao
from ergo import indexed_node_client
from util.util import is_uuid

from config import Config, Network


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
                    if dbd.config_height < state_daos[d][1]:
                        dao_config = dao.get_dao_config(d)
                        try:
                            edit_dao(
                                db,
                                dbd.id,
                                CreateOrUpdateDao(
                                    dao_name=state_daos[d][0],
                                    dao_short_description=dao_config["im.paideia.dao.desc"][
                                        "value"
                                    ]
                                    if "im.paideia.dao.desc" in dao_config
                                    else "",
                                    dao_url=urllib.parse.quote(dao_config["im.paideia.dao.url"][
                                        "value"
                                    ])
                                    if "im.paideia.dao.url" in dao_config and not any(c not in "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890-.%+" for c in urllib.parse.quote(dao_config["im.paideia.dao.url"]["value"]))
                                    else dbd.dao_url,
                                    dao_key=d,
                                    governance=CreateOrUpdateGovernance(
                                        quorum=int(
                                            dao_config["im.paideia.dao.quorum"]["value"]
                                        ),
                                        vote_duration__sec=int(
                                            dao_config["im.paideia.dao.min.proposal.time"][
                                                "value"
                                            ]
                                        )
                                        / 1000,
                                        support_needed=int(
                                            dao_config["im.paideia.dao.threshold"]["value"]
                                        ),
                                    ),
                                    tokenomics=CreateOrUpdateTokenomics(
                                        token_id=dao_config["im.paideia.dao.tokenid"][
                                            "value"
                                        ]
                                    ),
                                    config_height=state_daos[d][1],
                                    design=CreateOrUpdateDaoDesign(
                                        logo_url=dao_config["im.paideia.dao.logo"]["value"] if "im.paideia.dao.logo" in dao_config else None,
                                        show_banner=dao_config["im.paideia.dao.banner.enabled"]["value"] if "im.paideia.dao.banner.enabled" in dao_config else False,
                                        banner_url=dao_config["im.paideia.dao.banner"]["value"] if "im.paideia.dao.banner" in dao_config else None,
                                        show_footer=dao_config["im.paideia.dao.footer.enabled"]["value"] if "im.paideia.dao.footer.enabled" in dao_config else False,
                                        footer_text=dao_config["im.paideia.dao.footer"]["value"] if "im.paideia.dao.footer" in dao_config else None
                                    ),
                                    is_draft=False,
                                    is_published=True,
                                ),
                            )
                        except Exception as e:
                            logging.error(e)

            if not daoExistsInDB:
                dao_config = dao.get_dao_config(d)
                new_dao = create_dao(
                    db,
                    CreateOrUpdateDao(
                        dao_key=d,
                        config_height=state_daos[d][1],
                        dao_name=state_daos[d][0],
                        dao_short_description=dao_config["im.paideia.dao.desc"][
                            "value"
                        ]
                        if "im.paideia.dao.desc" in dao_config
                        else "",
                        dao_url=urllib.parse.quote(dao_config["im.paideia.dao.url"][
                                    "value"
                                ])
                                if "im.paideia.dao.url" in dao_config and not any(c not in "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890-.%+" for c in urllib.parse.quote(dao_config["im.paideia.dao.url"]["value"]))
                                else state_daos[d][0],
                        governance=CreateOrUpdateGovernance(
                            quorum=int(dao_config["im.paideia.dao.quorum"]["value"]),
                            vote_duration__sec=int(
                                dao_config["im.paideia.dao.min.proposal.time"]["value"]
                            )
                            / 1000,
                            support_needed=int(
                                dao_config["im.paideia.dao.threshold"]["value"]
                            ),
                        ),
                        tokenomics=CreateOrUpdateTokenomics(
                            token_id=dao_config["im.paideia.dao.tokenid"]["value"]
                        ),
                        design=CreateOrUpdateDaoDesign(
                            logo_url=dao_config["im.paideia.dao.logo"]["value"] if "im.paideia.dao.logo" in dao_config else None,
                            show_banner=dao_config["im.paideia.dao.banner.enabled"]["value"] if "im.paideia.dao.banner.enabled" in dao_config else False,
                            banner_url=dao_config["im.paideia.dao.banner"]["value"] if "im.paideia.dao.banner" in dao_config else None,
                            show_footer=dao_config["im.paideia.dao.footer.enabled"]["value"] if "im.paideia.dao.footer.enabled" in dao_config else False,
                            footer_text=dao_config["im.paideia.dao.footer"]["value"] if "im.paideia.dao.footer" in dao_config else None
                        ),
                        is_draft=False,
                        is_published=True,
                    ),
                )
                create_user_dao_profile(db, Config[Network].admin_id, new_dao.id)
        return get_all_daos(db)
    except Exception as e:
        logging.error(traceback.format_exc())
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
    "/treasury/{dao_id}",
    response_model=DaoTreasury,
    response_model_exclude_none=True,
    name="dao:treasury",
)
def get_treasury(dao_id: uuid.UUID, db=Depends(get_db)):
    try:
        db_dao = get_dao(db, dao_id)
        treasury_address = dao.get_dao_treasury(db_dao.dao_key)
        treasury_balance = indexed_node_client.get_balance(treasury_address)
        return DaoTreasury(address=treasury_address, balance=treasury_balance)
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/treasury/{dao_id}/transactions",
    response_model=TransactionHistory,
    response_model_exclude_none=True,
    name="dao:treasury-transactions",
)
def get_treasury_transactions(
    dao_id: uuid.UUID, offset: int = 0, limit: int = 10, db=Depends(get_db)
):
    try:
        # cached = cache.get("get_treasury_transactions_" + str(dao_id))
        # if cached:
        #    return cached
        db_dao = get_dao(db, dao_id)
        treasury_address = dao.get_dao_treasury(db_dao.dao_key)
        treasury_transactions = indexed_node_client.get_transactions(
            treasury_address, offset, limit
        )
        labeled_transactions = []
        for transaction in treasury_transactions["items"]:
            amounts = dict()
            label = "default"
            for input in transaction["inputs"]:
                input_box = indexed_node_client.get_box_by_id(input["boxId"])
                if input_box["address"] == treasury_address:
                    if "Erg" in amounts:
                        amounts["Erg"] -= input_box["value"]
                    else:
                        amounts["Erg"] = -1 * input_box["value"]
                    for asset in input_box["assets"]:
                        if asset["tokenId"] in amounts:
                            amounts[asset["tokenId"]] -= asset["amount"]
                        else:
                            amounts[asset["tokenId"]] = -1 * asset["amount"]
                else:
                    contract_sig = util.get_contract_sig(input_box["address"])
                    if "Profit" in contract_sig["className"]:
                        label = "Profit Sharing"
                    elif "Snapshot" in contract_sig["className"]:
                        label = "Stake Snapshot"
                    elif "Compound" in contract_sig["className"]:
                        label = "Stake Compound"
            for output in transaction["outputs"]:
                if output["address"] == treasury_address:
                    if "Erg" in amounts:
                        amounts["Erg"] += output["value"]
                    else:
                        amounts["Erg"] = output["value"]
                    for asset in output["assets"]:
                        if asset["tokenId"] in amounts:
                            amounts[asset["tokenId"]] += asset["amount"]
                        else:
                            amounts[asset["tokenId"]] = asset["amount"]
            amounts_labeled = []
            for amount_key in amounts.keys():
                if amount_key == "Erg" and amounts[amount_key] != 0:
                    amounts_labeled.append(
                        TokenAmount(
                            token_name="Erg", amount=amounts[amount_key] / 10**9
                        )
                    )
                elif amounts[amount_key] != 0:
                    token_info = indexed_node_client.get_token_info(amount_key)
                    amounts_labeled.append(
                        TokenAmount(
                            token_name=token_info["name"],
                            amount=amounts[amount_key]
                            / 10 ** (int(token_info["decimals"])),
                        )
                    )
            if label == "default":
                label = "Deposit" if amounts["Erg"] > 0 else "Withdrawal"
            labeled_transactions.append(
                Transaction(
                    transaction_id=transaction["id"],
                    label=label,
                    amount=amounts_labeled,
                    time=transaction["timestamp"],
                )
            )
        res = TransactionHistory(transactions=labeled_transactions).dict()
        cache.set("get_treasury_transactions_" + str(dao_id), res)
        return res
    except Exception as e:
        logging.error(traceback.format_exc())
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
        if is_uuid(query):
            dao = get_dao(db, uuid.UUID(query))
        else:
            dao = get_dao_by_url(db, query)
        if not dao:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return dao
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/{query}/config",
    response_model=dict[str, DaoConfigEntry],
    response_model_exclude_none=True,
    name="dao:get-dao-config",
)
def dao_get(
    query: str,
    db=Depends(get_db),
):
    """
    Get dao
    """
    try:
        d = None
        if is_uuid(query):
            d = get_dao(db, uuid.UUID(query))
        else:
            d = get_dao_by_url(db, query)
        if not d:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="dao not found"
            )
        return dao.get_dao_config(d.dao_key)
    except Exception as e:
        logging.error(traceback.format_exc())
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
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/on_chain_dao", response_model=SigningRequest, response_model_exclude_none=True, name="dao:create")
def dao_create_on_chain(
    create_dao_request: CreateOnChainDao,
    db=Depends(get_db),
):
    """
    Create a new dao
    """
    try:
        dao_url = create_dao_request.url
        if dao_url == "creation":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, content=f"Invalid DAO url: {dao_url}"
            )
        dao_exists = get_dao_by_url(db, dao_url)
        if dao_exists != None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, content=f"DAO url must be unique: {dao_url}"
            )
        unsigned_tx = dao.create_dao(create_dao_request)
        return SigningRequest(
            message="Create DAO transaction",
            unsigned_transaction=unsigned_tx
        )
    except Exception as e:
        logging.error(traceback.format_exc())
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
        logging.error(traceback.format_exc())
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
        logging.error(traceback.format_exc())
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
        logging.error(traceback.format_exc())
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
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
