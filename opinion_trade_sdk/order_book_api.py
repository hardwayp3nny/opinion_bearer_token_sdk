"""Order book helpers for Opinion Trade markets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from .errors import InvalidConfigError
from .network.http_client import RequestOptions, default_client
from .topic_api import OrderBookConfig

ORDER_BOOK_ENDPOINT = "https://proxy.opinion.trade:8443/api/bsc/api/v2/order/market/depth"


@dataclass
class OrderLevel:
    price: float
    amount: float
    total: float


@dataclass
class OrderBook:
    position: "OrderBookPosition"
    bids: List[OrderLevel]
    asks: List[OrderLevel]
    last_price: Optional[str]
    timestamp: str


@dataclass
class OrderBookPair:
    yes: OrderBook
    no: OrderBook


class OrderBookPosition(Enum):
    YES = "YES"
    NO = "NO"


class OrderBookApi:
    def __init__(self, config: OrderBookConfig) -> None:
        self.config = config

    async def get_order_book(self, position: OrderBookPosition) -> OrderBook:
        if position is OrderBookPosition.YES:
            symbol_type = "0"
            symbol = self.config.tokens.yes
        else:
            symbol_type = "1"
            if not self.config.tokens.no:
                raise InvalidConfigError("NO token not found")
            symbol = self.config.tokens.no

        url = (
            f"{ORDER_BOOK_ENDPOINT}?symbol_types={symbol_type}"
            f"&question_id={self.config.question_id}"
            f"&symbol={symbol}"
            f"&chainId={self.config.chain_id}"
        )

        response = await default_client().get(url, RequestOptions())
        return self._parse_order_book(position, response)

    async def get_both_order_books(self) -> OrderBookPair:
        yes = await self.get_order_book(OrderBookPosition.YES)
        no = await self.get_order_book(OrderBookPosition.NO)
        return OrderBookPair(yes=yes, no=no)

    def _parse_order_book(self, position: OrderBookPosition, value: Any) -> OrderBook:
        result = value.get("result") if isinstance(value, dict) else None
        if result is None and isinstance(value, dict):
            result = value.get("data")
        if result is None:
            result = {}

        bids = _parse_levels(result.get("bids"), descending=True)
        asks = _parse_levels(result.get("asks"), descending=False)
        last_price = result.get("last_price")
        if last_price is not None:
            last_price = str(last_price)

        timestamp = datetime.now(timezone.utc).isoformat()

        return OrderBook(
            position=position,
            bids=bids,
            asks=asks,
            last_price=last_price,
            timestamp=timestamp,
        )


def _parse_levels(value: Any, *, descending: bool) -> List[OrderLevel]:
    levels: List[OrderLevel] = []
    if isinstance(value, list):
        for entry in value:
            if isinstance(entry, list) and len(entry) >= 2:
                price_raw = entry[0]
                amount_raw = entry[1]
                price = _parse_float(price_raw)
                amount = _parse_float(amount_raw)
                total = price * amount
                levels.append(OrderLevel(price=price, amount=amount, total=total))

    levels.sort(key=lambda level: level.price, reverse=descending)
    return levels


def _parse_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


__all__ = [
    "OrderBookApi",
    "OrderBook",
    "OrderBookPair",
    "OrderBookPosition",
    "OrderLevel",
]
