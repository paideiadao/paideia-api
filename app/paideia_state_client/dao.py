import requests
from config import Config, Network
import typing as t

def get_all_daos():
    res = requests.get(Config[Network].paideia_state+'/dao')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def get_dao_config(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/config')
    if res.ok:
        resDict = {}
        for entry in res.json():
            resDict[entry["key"]] = {"valueType": entry["valueType"], "value": entry["value"]}
        return resDict
    else:
        raise Exception(res.text)
    
def get_dao_treasury(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/treasury')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def get_proposals(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/proposals')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)