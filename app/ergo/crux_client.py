import logging

import requests
from config import Config, Network
from db.schemas.util import Price


def get_token_info(token_id: str):
    res = requests.get(Config[Network].crux_api + "/crux/token_info/" + token_id)
    if res.ok:
        return res.json()
    else:
        logging.error("Failed get token info from crux api: " + res.text)


def get_erg_price() -> Price | None:
    res = requests.get(Config[Network].crux_api + "/coingecko/erg_price")
    if res.ok:
        return res.json()
    else:
        logging.error("Failed get erg price from crux api: " + res.text)
