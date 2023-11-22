import requests

from cache.cache import cache
from config import Config, Network

def get_token_info(token_id: str):
    cached = cache.get("get_token_info_" + token_id)
    if cached:
        return cached
    #res = requests.get(Config[Network].node+":9053/blockchain/token/byId/"+token_id)
    res = requests.get("https://api.cruxfinance.io/crux/token_info/"+token_id)
    if res.ok:      
        #temp fix start#
        resJson = res.json()
        token_info = {
        "id": token_id,
        "boxId": token_id,
        "emissionAmount": resJson["minted"],
        "name": resJson["token_name"],
        "description": resJson["token_description"],
        "decimals": resJson["decimals"]
        }
        ##temp fix end##
        
        #token_info = res.json()
        
        cache.set("get_token_info_" + token_id, token_info)
        return token_info
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