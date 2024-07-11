from pydantic import BaseModel

import typing as t


class AddressList(BaseModel):
    addresses: t.List[str]


class AddressTokenList(BaseModel):
    addresses: t.List[str]
    tokens: t.List[str]


class TokenPriceRangeDataPoint(BaseModel):
    high: t.Optional[float]
    low: t.Optional[float]
    open: t.Optional[float]
    close: t.Optional[float]
    volume: t.Optional[float]
    start_time: str = "2022-09-07T17:12:05"
    end_time: str = "2022-09-07T17:12:05"


class TokenPriceRangeSummaryDataPoint(TokenPriceRangeDataPoint):
    abs_change: float = 0
    change_percentage: float = 0


class TokenPriceHistorySummary(BaseModel):
    hour_24: TokenPriceRangeSummaryDataPoint
    yesterday: TokenPriceRangeSummaryDataPoint
    day_7: TokenPriceRangeSummaryDataPoint
    day_30: TokenPriceRangeSummaryDataPoint
    day_90: TokenPriceRangeSummaryDataPoint
    week_52: TokenPriceRangeSummaryDataPoint
    all_time: TokenPriceRangeSummaryDataPoint


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
    token_price_history_summary: TokenPriceHistorySummary
    market_cap: TokenMarketCap
    token_supply: TokenSupplyStats
    token_markets: t.List[TokenMarketSpecificStats]
