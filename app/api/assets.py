import requests

from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from ergo.schemas import AddressList, TokenStats, AddressTokenList
from config import Config, Network
from cache.cache import cache


CFG = Config[Network]
assets_router = r = APIRouter()


# constants
TOKEN_CONFIG = {
    "paideia": {
        "token_id": "1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489",
        "stake_tree": "101f040004000e2012bbef36eaa5e61b64d519196a1e8ebea360f18aba9b02d2a21b16f26208960f040204000400040001000e20b682ad9e8c56c5a0ba7fe2d3d9b2fbd40af989e8870628f4a03ae1022d36f0910402040004000402040204000400050204020402040604000100040404020402010001010100040201000100d807d601b2a4730000d6028cb2db6308720173010001d6039372027302d604e4c6a70411d605e4c6a7050ed60695ef7203ed93c5b2a4730300c5a78fb2e4c6b2a57304000411730500b2e4c6720104117306007307d6079372027308d1ecec957203d80ad608b2a5dc0c1aa402a7730900d609e4c672080411d60adb63087208d60bb2720a730a00d60cdb6308a7d60db2720c730b00d60eb2720a730c00d60fb2720c730d00d6107e8c720f0206d611e4c6720104119683090193c17208c1a793c27208c2a793b27209730e009ab27204730f00731093e4c67208050e720593b27209731100b27204731200938c720b018c720d01938c720b028c720d02938c720e018c720f01937e8c720e02069a72109d9c7eb272117313000672107eb27211731400067315957206d801d608b2a5731600ed72079593c27208c2a7d801d609c67208050e95e67209ed93e472097205938cb2db6308b2a57317007318000172057319731a731b9595efec7206720393c5b2a4731c00c5a7731d7207731e",
        "vest_tree": "",
        "proxy_address": "245957934c20285ada547aa8f2c8e6f7637be86a1985b3e4c36e4e1ad8ce97ab",
    },
}


@r.post("/locked/{token}", name="assets:locked-token")
def locked_tokens(token: str, req: AddressList):
    try:
        token = token.lower()
        address_list = req.addresses
        if token not in TOKEN_CONFIG:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content="token config not found"
            )
        # call to danaides service
        ret = requests.post(
            f"{CFG.danaides_api}/token/locked",
            json={
                "addresses": address_list,
                "tokens": [
                    {
                        "token_id": TOKEN_CONFIG[token]["token_id"],
                        "stake_tree": TOKEN_CONFIG[token]["stake_tree"],
                        "vest_tree": TOKEN_CONFIG[token]["vest_tree"],
                        "proxy_address": TOKEN_CONFIG[token]["proxy_address"],
                    }
                ]
            },
        )
        # return as json
        return ret.json()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/token-exists", name="assets:deprecated")
def token_check_deprecated(req: AddressTokenList):
    """
    DEPRECATED
    """
    return token_check(req)


@r.post("/token_check", name="assets:check-token-exists")
def token_check(req: AddressTokenList):
    try:
        cache_key = "token_check_" + hash_string_list(req.tokens) +  "_" + hash_string_list(req.addresses)
        cached = cache.get(cache_key)
        if cached:
            return cached
        # call to danaides service
        ret = requests.post(
            f"{CFG.danaides_api}/token/exists",
            json={
                "addresses": req.addresses,
                "tokens": req.tokens,
            },
        )
        if ret.ok:
            cache.set(cache_key, ret.json())
        return ret.json()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get("/token_stats/{token_id}", response_model=TokenStats, name="assets:get-token-stats")
def get_token_stats(token_id: str):
    try:
        resp = cache.get(f"token_stats_cache_{token_id}")
        if not resp:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, content=f"token is not part of a dao"
            )
        return resp
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


def get_token_name_from_id(token_id):
    for token in TOKEN_CONFIG:
        if TOKEN_CONFIG[token]["token_id"] == token_id:
            return token
    return "unknown"


def hash_string_list(address_list):
    sorted_al = tuple(sorted(address_list))
    return str(hash(sorted_al))
