from pydantic import BaseModel

import datetime
import typing as t


class AddressList(BaseModel):
    addresses: t.List[str]


class TokenPriceRangeDataPoint(BaseModel):
    high: float
    low: float
    open: float
    close: float
    volume: t.Optional[float]
    start_time: datetime.datetime
    end_time: datetime.datetime


class TokenPriceRangeSummaryDataPoint(TokenPriceRangeDataPoint):
    abs_change: float
    change_percentage: float


class TokenPriceHistorySummary(BaseModel):
    hour_24: t.Optional[TokenPriceRangeSummaryDataPoint]
    yesterday: t.Optional[TokenPriceRangeSummaryDataPoint]
    day_7: t.Optional[TokenPriceRangeSummaryDataPoint]
    day_30: t.Optional[TokenPriceRangeSummaryDataPoint]
    day_90: t.Optional[TokenPriceRangeSummaryDataPoint]
    week_52: t.Optional[TokenPriceRangeSummaryDataPoint]
    all_time: t.Optional[TokenPriceRangeSummaryDataPoint]


class TokenMarketCap(BaseModel):
    market_cap: t.Optional[float]
    diluted_market_cap: float


class TokenSupplyStats(BaseModel):
    total_supply: t.Optional[float]
    max_supply: float


class TokenMarketSpecificStats(BaseModel):
    source: str = "spectrum.fi"
    pair: str = "Paideia/ERG"
    price: float
    volume: t.Optional[float]
    liquidity: t.Optional[float]


class TokenStats(BaseModel):
    token_id: str = "1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489"
    token_name: str = "Paideia"
    price: float
    token_ohclv_1h: t.List[TokenPriceRangeDataPoint] = []
    token_price_history_summary: TokenPriceHistorySummary
    market_cap: TokenMarketCap
    token_supply: TokenSupplyStats
    token_markets: t.List[TokenMarketSpecificStats]
