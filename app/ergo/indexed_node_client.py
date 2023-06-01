import requests

from config import Config, Network

def get_token_info(token_id: str):
    res = requests.get(Config[Network].node+":9053/blockchain/token/byId/"+token_id)
    if res.ok:
        return res.json()
    else:
        return None
    
def get_balance(address: str):
    res = requests.post(Config[Network].node+":9053/blockchain/balance", json=address)
    if res.ok:
        return res.json()
    else:
        return None