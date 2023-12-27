import requests
from config import Config, Network
import typing as t
import logging

def get_proposal(daoKey: str, index: int):
    res = requests.get(Config[Network].paideia_state+'/proposal/' + daoKey + '/' + str(index))
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def cast_vote(daoKey: str, stakeKey: str, proposalIndex: int, votes: t.List[int], mainAddress: str, allAddresses: t.List[str]):
    res = requests.post(Config[Network].paideia_state+'/proposal/vote', json={
        "daoKey": daoKey,
        "stakeKey": stakeKey,
        "proposalIndex": proposalIndex,
        "votes": votes,
        "userAddress": mainAddress,
        "userAddresses": allAddresses
    })
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def create_proposal(daoKey: str, name: str, stakeKey: str, mainAddress: str, allAddresses: t.List[str], endTime: int, sendFundsActions: t.List[dict], updateConfigActions: t.List[dict]):
    logging.info({
        "daoKey": daoKey,
        "name": name,
        "voteKey": stakeKey,
        "userAddress": mainAddress,
        "userAddresses": allAddresses,
        "endTime": endTime,
        "sendFundsActions": sendFundsActions,
        "updateConfigActions": updateConfigActions
    })
    res = requests.post(Config[Network].paideia_state+'/proposal', json={
        "daoKey": daoKey,
        "name": name,
        "voteKey": stakeKey,
        "userAddress": mainAddress,
        "userAddresses": allAddresses,
        "endTime": endTime,
        "sendFundsActions": sendFundsActions,
        "updateConfigActions": updateConfigActions
    })
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)