import requests
from config import Config, Network
import typing as t

def stake(daoKey: str, amount: int, mainAddress: str, allAddresses: t.List[str]):
    res = requests.post(Config[Network].paideia_state+'/stake', json={
        "daoKey": daoKey,
        "stakeAmount": amount,
        "userAddress": mainAddress,
        "userAddresses": allAddresses
    })
    if res.ok:
        return res.json()
    else:
        return None