import requests

from config import Config, Network

def get_token_info(token_id: str):
    res = requests.get(Config[Network].node+":9053/blockchain/token/byId/"+token_id)
    if res.ok:
        return res.json()
    else:
        return None
    
def get_balance(address: str):
    res = requests.post(Config[Network].node+":9053/blockchain/balance", data=address)
    if res.ok:
        return res.json()
    else:
        return None
    
def get_transactions(address: str, offset: int, limit: int):
    res = requests.post(Config[Network].node+':9053/blockchain/transaction/byAddress?offset='+str(offset)+'&limit='+str(limit), data=address)
    if res.ok:
        return res.json()
    else:
        return None
    
def get_box_by_id(boxId: str):
    res = requests.get(Config[Network].node+':9053/blockchain/box/byId/'+boxId)
    if res.ok:
        return res.json()
    else:
        return None