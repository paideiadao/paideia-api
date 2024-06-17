import requests
import logging

from config import Config, Network

def get_token_info(token_id: str):
    res = requests.get(Config[Network].crux_api + "/crux/token_info/" + token_id)
    if res.ok:
        return res.json()
    else:
        logging.error("Failed get token info from crux api: " + res.text)
