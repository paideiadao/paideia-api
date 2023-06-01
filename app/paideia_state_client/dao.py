import requests
from config import Config, Network
import typing as t

def get_all_daos():
    res = requests.get(Config[Network].paideia_state+'/dao')
    if res.ok:
        return res.json()
    else:
        return None
    
def get_dao_config(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/config')
    if res.ok:
        return res.json()
    else:
        return None