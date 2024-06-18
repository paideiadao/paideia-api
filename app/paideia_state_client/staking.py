import requests
from db.schemas.staking import NewStakeRecord
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
        raise Exception(res.text)
    
def get_dao_stake(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/stake/'+daoKey)
    if res.ok:
        return res.json()
    else:
        return None
    
def get_stake(daoKey: str, stakeKeys: t.Set[str]):
    res = requests.post(Config[Network].paideia_state+'/stake/'+daoKey, json = {"potentialKeys": stakeKeys})
    if res.ok:
        return res.json()
    else:
        return None
    
def add_stake(daoKey: str, stakeKey: str, amount: int, mainAddress: str, allAddresses: t.List[str]):
    res = requests.post(Config[Network].paideia_state+'/stake/add', json={
        "daoKey": daoKey,
        "stakeKey": stakeKey,
        "addStakeAmount": amount,
        "userAddress": mainAddress,
        "userAddresses": allAddresses
    })
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def unstake(daoKey: str, stakeKey: str, newStakeRecord: NewStakeRecord, mainAddress: str, allAddresses: t.List[str]):
    res = requests.post(Config[Network].paideia_state+'/stake/remove', json={
        "daoKey": daoKey,
        "stakeKey": stakeKey,
        "newStakeRecord": newStakeRecord.dict(),
        "userAddress": mainAddress,
        "userAddresses": allAddresses
    })
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)