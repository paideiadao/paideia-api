"""
Notes: Where the data exists
- erg price -> get from ergopad.io
- token basic data -> get from explorer (name, desc) etc
- price history for candles -> spectrum.fi
- tvl/volume -> spectrum.fi
- danaides?

Examples:
- https://api.ergopad.io/asset/price/ergo
- https://api.ergoplatform.com/api/v1/tokens/1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489
- https://api.spectrum.fi/v1/amm/pools/stats
- https://api.spectrum.fi/v1/amm/pool/666be5df835a48b99c40a395a8aa3ea6ce39ede2cd77c02921d629b9baad8200/chart

Todo: Clean this up to a more unified way of getting data
"""

import requests
from sqlalchemy.orm import Session

from config import Config, Network
from db.session import get_db
from db.models.tokenomics import Tokenomics
from ergo.schemas import TokenStats


CFG = Config[Network]
ERG_ID = "0000000000000000000000000000000000000000000000000000000000000000"


class BaseDataProvider:
    # temp dependencies config
    ERGOPAD_API = "https://api.ergopad.io"
    EXPLORER_API = "https://api.ergoplatform.com/api/v1"
    SPECTRUM_API = "https://api.spectrum.fi/v1"
    DANAIDES_API = CFG.danaides_api

    @staticmethod
    def get_ergo_price():
        try:
            resp = requests.get(
                f"{BaseDataProvider.ERGOPAD_API}/asset/price/ergo").json()
            return resp
        except Exception as e:
            print(e)

    @staticmethod
    def get_token_details_by_id(token_id: str):
        try:
            resp = requests.get(
                f"{BaseDataProvider.EXPLORER_API}/tokens/{token_id}").json()
            return resp
        except Exception as e:
            print(e)

    @staticmethod
    def get_spectrum_pools():
        try:
            resp = requests.get(
                f"{BaseDataProvider.SPECTRUM_API}/amm/pools/stats").json()
            return resp
        except Exception as e:
            print(e)

    @staticmethod
    def get_pool_price_history(pool_id: str):
        try:
            resp = requests.get(
                f"{BaseDataProvider.SPECTRUM_API}/amm/pool/{pool_id}/chart").json()
            return resp
        except Exception as e:
            print(e)

    @staticmethod
    def get_dao_token_ids(db: Session = next(get_db())):
        try:
            resp = list(map(lambda x: x[0], db.query(Tokenomics.token_id).all()))
            return resp
        except Exception as e:
            print(e)


class TokenDataBuilder:
    @staticmethod
    def get_max_pool_by_token_id(token_id: str):
        pools = BaseDataProvider.get_spectrum_pools()
        if not pools:
            return pools
        filter_pools = list(filter(lambda pool: pool["lockedX"]["id"] == token_id or pool["lockedY"]["id"] == token_id, pools))
        filter_pools = list(filter(lambda pool: pool["lockedX"]["id"] == ERG_ID, filter_pools))
        if len(filter_pools) == 0:
            return None
        max_pool = filter_pools[0]
        for pool in filter_pools:
            if pool["lockedX"]["amount"] > max_pool["lockedX"]["amount"]:
                max_pool = pool
        return max_pool


    @staticmethod
    def build(token_id: str):
        erg_usd = BaseDataProvider.get_ergo_price()
        # we can fill basic details from this
        token_details = BaseDataProvider.get_token_details_by_id(token_id)
        pool = TokenDataBuilder.get_max_pool_by_token_id(token_id)
        if not pool:
            return None
        price_chart = BaseDataProvider.get_pool_price_history(pool["id"])
        # format price_chart data into required stuff
        # todo: return TokenStats
        return None


def test():
    print(BaseDataProvider.get_ergo_price())
    print(BaseDataProvider.get_dao_token_ids())
    print(BaseDataProvider.get_token_details_by_id("1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489"))
    print(BaseDataProvider.get_spectrum_pools())
    print(BaseDataProvider.get_pool_price_history("666be5df835a48b99c40a395a8aa3ea6ce39ede2cd77c02921d629b9baad8200"))
