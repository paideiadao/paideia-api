import datetime
import requests
import logging
import traceback
from sqlalchemy.orm import Session

from config import Config, Network
from cache.cache import cache
from db.session import get_db
from db.models.tokenomics import Tokenomics
from ergo.schemas import TokenStats, TokenPriceHistorySummary, TokenSupplyStats, TokenMarketCap, TokenPriceRangeSummaryDataPoint, TokenMarketSpecificStats


CFG = Config[Network]


class DataProviderException(Exception):
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
            raise DataProviderException(e)


class BaseDataProvider:
    CRUX_API = CFG.crux_api

    @staticmethod
    def get_ergo_price():
        try:
            resp = requests.get(
                f"{BaseDataProvider.CRUX_API}/coingecko/erg_price"
            )
            if (resp.status_code != 200):
                raise Exception(resp.text)
            return resp.json()
        except Exception as e:
            raise DataProviderException(e)

    @staticmethod
    def get_token_details_by_id(token_id: str):
        try:
            resp = requests.get(
                f"{BaseDataProvider.CRUX_API}/crux/token_info/{token_id}"
            )
            if (resp.status_code != 200):
                raise Exception(resp.text)
            return resp.json()
        except Exception as e:
            raise DataProviderException(e)

    @staticmethod
    def get_ohclv_by_token_name(token_name: str, start_time: int, end_time: int, resolution: str, countback: int):
        try:
            resp = requests.get(
                f"{BaseDataProvider.CRUX_API}/trading_view/history?symbol={token_name}_ERG&resolution={resolution}&from={start_time}&to={end_time}&countback={countback}"
            )
            if (resp.status_code != 200):
                raise Exception(resp.text)
            return resp.json()
        except Exception as e:
            raise DataProviderException(e)


class TokenDataBuilder:
    @staticmethod
    def summarize_last_hours(token_name: str, end_time: int, resolution: str, countback: int):
        ohclv = BaseDataProvider.get_ohclv_by_token_name(token_name, 0, end_time, resolution, countback)
        if ohclv["s"] != "ok" or len(ohclv["t"]) == 0:
            return TokenPriceRangeSummaryDataPoint()

        summary = TokenPriceRangeSummaryDataPoint(
            high=max(ohclv["h"]),
            low=min(ohclv["l"]),
            open=ohclv["o"][0],
            close=ohclv["c"][-1],
            volume=sum(ohclv["v"]),
            start_time=ohclv["t"][0],
            end_time=ohclv["t"][-1],
            abs_change=ohclv["c"][-1] - ohclv["o"][0],
            change_percentage=(ohclv["c"][-1] - ohclv["o"][0]) / (ohclv["o"][0])
        )
        return summary

    @staticmethod
    def build_stats_for_token_id(token_id: str):
        erg_usd = BaseDataProvider.get_ergo_price()["price"]
        token_details = BaseDataProvider.get_token_details_by_id(token_id)
        # we can fill basic details from this
        token_price_in_erg = token_details["value_in_erg"]
        token_price = token_price_in_erg * erg_usd

        # token_price_history_summary
        now = int(datetime.datetime.now().timestamp())
        hr = 60 * 60
        day = 24 * hr
        token_price_history_summary = TokenPriceHistorySummary(
            hour_24=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "60", 24
            ),
            yesterday=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now - day, "60", 24
            ),
            day_7=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "1D", 7
            ),
            day_30=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "1D", 30
            ),
            day_90=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "1M", 3
            ),
            week_52=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "1M", 12
            ),
            all_time=TokenDataBuilder.summarize_last_hours(
                token_details["token_name"], now, "1M", 60
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
            token_price_history_summary=token_price_history_summary,
            market_cap=market_cap,
            token_supply=token_supply,
            token_markets=[
                TokenMarketSpecificStats(
                    source="spectrum.fi",
                    pair=token_details["token_name"] + "_ERG",
                    price=token_price_in_erg,
                    volume=token_price_history_summary.all_time.volume
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
