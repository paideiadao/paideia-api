import requests
from cache.cache import cache
from config import Config, Network
import typing as t


def get_contract_sig(address: str):
    if len(address) == 52 and address[0] == "9":
        return None
    cached = cache.get("get_contract_sig_" + str(address))
    if cached:
        return cached
    res = requests.post(
        Config[Network].paideia_state + "/util/contractSignature",
        json={"contractAddress": address},
    )
    if res.ok:
        cache.set("get_contract_sig_" + str(address), res.json())
        return res.json()
    else:
        return None
