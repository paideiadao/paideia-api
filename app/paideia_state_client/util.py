import requests
from config import Config, Network
import typing as t
 
def get_contract_sig(address: str):
    res = requests.post(Config[Network].paideia_state+'/util/contractSignature', json={
        "contractAddress": address
    })
    if res.ok:
        return res.json()
    else:
        return None