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

import datetime
import requests
import logging
import traceback
from sqlalchemy.orm import Session

from config import Config, Network
from cache.cache import cache
from db.session import get_db
from db.models.tokenomics import Tokenomics
from ergo.schemas import TokenStats, TokenPriceHistorySummary, TokenSupplyStats, TokenMarketCap, TokenPriceRangeDataPoint, TokenPriceRangeSummaryDataPoint, TokenMarketSpecificStats


CFG = Config[Network]
ERG_ID = "0000000000000000000000000000000000000000000000000000000000000000"
PAIDEIA_TOKEN_ID = "1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489"


class DataProviderException(Exception):
    pass


class BuilderException(Exception):
    pass


class LocalDataProvider:
    @staticmethod
    def get_dao_token_ids(db: Session = next(get_db())):
        try:
            resp = list(
                map(lambda x: x[0], db.query(Tokenomics.token_id).all())
            )
            return resp
        except Exception as e:
            logging.error(traceback.format_exc())


class BaseDataProvider:
    SPECTRUM_API = "https://api.spectrum.fi/v1"
    CRUX_API = "https://api.cruxfinance.io"

    @staticmethod
    def get_ergo_price():
        try:
            resp = requests.get(
                f"{BaseDataProvider.CRUX_API}/coingecko/erg_price"
            ).json()
            return resp
        except Exception as e:
            logging.error(traceback.format_exc())

    @staticmethod
    def get_token_details_by_id(token_id: str):
        try:
            resp = requests.get(
                f"{BaseDataProvider.CRUX_API}/crux/token_info/{token_id}"
            ).json()
            return resp
        except Exception as e:
            logging.error(traceback.format_exc())

    @staticmethod
    def get_spectrum_pools():
        try:
            resp = requests.get(
                f"{BaseDataProvider.SPECTRUM_API}/amm/pools/stats"
            ).json()
            return resp
        except Exception as e:
            logging.error(traceback.format_exc())

    @staticmethod
    def get_pool_price_history(pool_id: str):
        try:
            resp = requests.get(
                f"{BaseDataProvider.SPECTRUM_API}/amm/pool/{pool_id}/chart"
            ).json()
            return resp
        except Exception as e:
            logging.error(traceback.format_exc())


class TokenDataBuilder:
    @staticmethod
    def get_max_pool_by_token_id(token_id: str):
        pools = BaseDataProvider.get_spectrum_pools()
        if not pools:
            return pools
        filter_pools = list(filter(
            lambda pool: pool["lockedX"]["id"] == token_id or pool["lockedY"]["id"] == token_id, pools
        ))
        filter_pools = list(
            filter(lambda pool: pool["lockedX"]["id"] == ERG_ID, filter_pools)
        )
        if len(filter_pools) == 0:
            raise BuilderException(
                f"error: token_id={token_id}, message=required pool not found"
            )
        max_pool = filter_pools[0]
        for pool in filter_pools:
            if pool["lockedX"]["amount"] > max_pool["lockedX"]["amount"]:
                max_pool = pool
        return max_pool

    @staticmethod
    def summarize_last_hours(price_history, start_time, end_time):
        price_history = list(map(
            lambda x: (
                1 / x["price"], x["timestamp"] / 1000),
            price_history["market"]["dataPoints"]
        ))
        price_history.sort(key=(lambda x: x[1]))
        bucket = []
        for dp in price_history:
            if start_time <= dp[1] and dp[1] <= end_time:
                bucket.append(dp)
        if len(bucket) == 0:
            return TokenPriceRangeSummaryDataPoint(
                start_time=start_time,
                end_time=end_time,
            )
        summary = TokenPriceRangeSummaryDataPoint(
            high=max(bucket)[0],
            low=min(bucket)[0],
            open=bucket[0][0],
            close=bucket[-1][0],
            start_time=start_time,
            end_time=end_time,
            abs_change=bucket[-1][0]-bucket[0][0],
            change_percentage=(bucket[-1][0]-bucket[0][0]) / (bucket[0][0])
        )
        return summary

    @staticmethod
    def build_stats_for_token_id(token_id: str):
        erg_usd = BaseDataProvider.get_ergo_price()["price"]
        # we can fill basic details from this
        token_details = BaseDataProvider.get_token_details_by_id(token_id)
        token_price_in_erg = token_details["value_in_erg"]
        token_price = token_price_in_erg * erg_usd

        # TODO: get price performance summary from crux instead
        pool = TokenDataBuilder.get_max_pool_by_token_id(token_id)
        price_chart = BaseDataProvider.get_pool_price_history(pool["id"])
        price_history = {
            "id": token_id,
            "price": token_price_in_erg,
            "market": {
                "dataPoints": price_chart,
            }
        }
        # token_price_history_summary
        now = datetime.datetime.now().timestamp()
        hr = 60 * 60
        day = 24 * hr
        week = 7 * day
        token_price_history_summary = TokenPriceHistorySummary(
            hour_24=TokenDataBuilder.summarize_last_hours(
                price_history, now - day, now
            ),
            yesterday=TokenDataBuilder.summarize_last_hours(
                price_history, now - 2 * day, now - 1 * day
            ),
            day_7=TokenDataBuilder.summarize_last_hours(
                price_history, now - 7 * day, now
            ),
            day_30=TokenDataBuilder.summarize_last_hours(
                price_history, now - 30 * day, now
            ),
            day_90=TokenDataBuilder.summarize_last_hours(
                price_history, now - 90 * day, now
            ),
            week_52=TokenDataBuilder.summarize_last_hours(
                price_history, now - 52 * week, now
            ),
            all_time=TokenDataBuilder.summarize_last_hours(
                price_history, 0, now
            )
        )

        # market_cap
        market_cap = TokenMarketCap(
            market_cap=token_price * token_details["liquid_supply"],
            diluted_market_cap=token_price * token_details["minted"]
        )
        # token_supply
        token_supply = TokenSupplyStats(
            total_supply=token_details["liquid_supply"],
            max_supply=token_details["minted"]
        )

        return TokenStats(
            token_id=token_id,
            token_name=token_details["token_name"],
            price=token_price,
            token_ohclv_1h=[],
            token_price_history_summary=token_price_history_summary,
            market_cap=market_cap,
            token_supply=token_supply,
            token_markets=[
                TokenMarketSpecificStats(
                    source="spectrum.fi",
                    pair=token_details["token_name"] + "_ERG",
                    price=token_price_in_erg,
                )
            ]
        )


def update_token_data_cache():
    token_ids = LocalDataProvider.get_dao_token_ids()
    for token_id in token_ids:
        try:
            token_stats = TokenDataBuilder.build_stats_for_token_id(
                token_id
            ).dict()
            cache.set(f"token_stats_cache_{token_id}", token_stats)
            logging.info(f"token_stats_cache_{token_id}_updated")
        except Exception as e:
            logging.error(traceback.format_exc())
