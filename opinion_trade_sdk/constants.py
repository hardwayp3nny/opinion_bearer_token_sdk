"""Constant values and enumerations used across the SDK."""

from __future__ import annotations

from enum import Enum, IntEnum

CHAIN_ID: int = 56
EXCHANGE_ADDRESS: str = "0x5F45344126D6488025B0b84A3A8189F2487a7246"
COLLATERAL_TOKEN_ADDRESS: str = "0x55d398326f99059fF775485246999027B3197955"
COLLATERAL_TOKEN_DECIMAL: int = 18

API_BASE_URL: str = "https://proxy.opinion.trade:8443/api/bsc/api"


class ApiEndpoints:
    SUBMIT_ORDER = "/v2/order"
    QUERY_ORDERS = "/v2/order"
    QUERY_TRADES = "/v2/trade"
    CANCEL_ORDER = "/v1/order/cancel/order"


class Side(IntEnum):
    BUY = 0
    SELL = 1

    def as_str(self) -> str:
        return "BUY" if self is Side.BUY else "SELL"


class SignatureType(IntEnum):
    POLY_GNOSIS_SAFE = 2


class MarketType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"


class TradingMethod(IntEnum):
    MARKET = 1
    LIMIT = 2


class VolumeType(Enum):
    SHARES = "Shares"
    AMOUNT = "Amount"


class YesOrNo(IntEnum):
    YES = 1
    NO = 2


class OrderQueryType(IntEnum):
    OPEN = 1
    CLOSED = 2


class OrderStatus(IntEnum):
    OPEN = 1
    FILLED = 2
    CANCELLED = 3


class TradeType(Enum):
    SPLIT = "Split"
    BUY = "Buy"
    SELL = "Sell"
    MERGE = "Merge"


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

__all__ = [
    "CHAIN_ID",
    "EXCHANGE_ADDRESS",
    "COLLATERAL_TOKEN_ADDRESS",
    "COLLATERAL_TOKEN_DECIMAL",
    "API_BASE_URL",
    "ApiEndpoints",
    "Side",
    "SignatureType",
    "MarketType",
    "TradingMethod",
    "VolumeType",
    "YesOrNo",
    "OrderQueryType",
    "OrderStatus",
    "TradeType",
    "ZERO_ADDRESS",
]