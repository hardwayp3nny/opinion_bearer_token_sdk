"""Dataclasses for API payloads and responses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SubmitOrderPayload:
    topic_id: int
    contract_address: str
    price: str
    trading_method: int
    salt: str
    maker: str
    signer: str
    taker: str
    token_id: str
    maker_amount: str
    taker_amount: str
    expiration: str
    nonce: str
    fee_rate_bps: str
    side: str
    signature_type: str
    signature: str
    timestamp: int
    sign: str
    safe_rate: str
    order_exp_time: str
    currency_address: str
    chain_id: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topicId": self.topic_id,
            "contractAddress": self.contract_address,
            "price": self.price,
            "tradingMethod": self.trading_method,
            "salt": self.salt,
            "maker": self.maker,
            "signer": self.signer,
            "taker": self.taker,
            "tokenId": self.token_id,
            "makerAmount": self.maker_amount,
            "takerAmount": self.taker_amount,
            "expiration": self.expiration,
            "nonce": self.nonce,
            "feeRateBps": self.fee_rate_bps,
            "side": self.side,
            "signatureType": self.signature_type,
            "signature": self.signature,
            "timestamp": self.timestamp,
            "sign": self.sign,
            "safeRate": self.safe_rate,
            "orderExpTime": self.order_exp_time,
            "currencyAddress": self.currency_address,
            "chainId": self.chain_id,
        }


@dataclass
class OrderData:
    amount: str
    chain_id: int
    created_at: int
    currency_address: str
    expiration: int
    filled: str
    finish_amount: str
    finish_share: str
    mutil_title: str
    mutil_topic_id: int
    order_id: int
    outcome: str
    outcome_side: int
    price: str
    profit: str
    side: int
    status: int
    topic_id: int
    topic_title: str
    total_price: str
    trading_method: int
    trans_no: str
    raw: Dict[str, Any]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "OrderData":
        data = data or {}
        return OrderData(
            amount=_string_or_number(_get_field(data, "amount")) or "",
            chain_id=int(_get_field(data, "chain_id") or 0),
            created_at=int(_get_field(data, "created_at") or 0),
            currency_address=_string_or_number(_get_field(data, "currency_address")) or "",
            expiration=int(_get_field(data, "expiration") or 0),
            filled=_string_or_number(_get_field(data, "filled")) or "",
            finish_amount=_string_or_number(_get_field(data, "finish_amount")) or "",
            finish_share=_string_or_number(_get_field(data, "finish_share")) or "",
            mutil_title=_string_or_number(_get_field(data, "mutil_title")) or "",
            mutil_topic_id=int(_get_field(data, "mutil_topic_id") or 0),
            order_id=int(_get_field(data, "order_id") or 0),
            outcome=_string_or_number(_get_field(data, "outcome")) or "",
            outcome_side=int(_get_field(data, "outcome_side") or 0),
            price=_string_or_number(_get_field(data, "price")) or "",
            profit=_string_or_number(_get_field(data, "profit")) or "",
            side=int(_get_field(data, "side") or 0),
            status=int(_get_field(data, "status") or 0),
            topic_id=int(_get_field(data, "topic_id") or 0),
            topic_title=_string_or_number(_get_field(data, "topic_title")) or "",
            total_price=_string_or_number(_get_field(data, "total_price")) or "",
            trading_method=int(_get_field(data, "trading_method") or 0),
            trans_no=_string_or_number(_get_field(data, "trans_no")) or "",
            raw=data,
        )


@dataclass
class SubmitOrderResult:
    order_data: Optional[OrderData]
    raw: Dict[str, Any]

    @staticmethod
    def from_dict(data: Optional[Dict[str, Any]]) -> "SubmitOrderResult":
        data = data or {}
        order_data_raw = data.get("orderData") or data.get("order_data")
        order_data = (
            OrderData.from_dict(order_data_raw)
            if isinstance(order_data_raw, dict)
            else None
        )
        return SubmitOrderResult(order_data=order_data, raw=data)


@dataclass
class SubmitOrderResponse:
    errno: int
    errmsg: str
    result: SubmitOrderResult
    raw: Dict[str, Any]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SubmitOrderResponse":
        data = data or {}
        return SubmitOrderResponse(
            errno=int(data.get("errno") or 0),
            errmsg=str(data.get("errmsg") or ""),
            result=SubmitOrderResult.from_dict(
                data.get("result") if isinstance(data.get("result"), dict) else {}
            ),
            raw=data,
        )


@dataclass
class CancelOrderResult:
    success: bool
    raw: Dict[str, Any]

    @staticmethod
    def from_dict(data: Optional[Dict[str, Any]]) -> "CancelOrderResult":
        data = data or {}
        success_value = data.get("result")
        return CancelOrderResult(success=bool(success_value), raw=data)


@dataclass
class CancelOrderResponse:
    errno: int
    errmsg: str
    result: CancelOrderResult
    raw: Dict[str, Any]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CancelOrderResponse":
        data = data or {}
        return CancelOrderResponse(
            errno=int(data.get("errno") or 0),
            errmsg=str(data.get("errmsg") or ""),
            result=CancelOrderResult.from_dict(
                data.get("result") if isinstance(data.get("result"), dict) else {}
            ),
            raw=data,
        )


@dataclass
class TradeRecord:
    status: int = 0
    shares: str = "0"
    last_price: str = "0"
    side: str = ""
    fee: str = "0"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TradeRecord":
        return TradeRecord(
            status=int(data.get("status", 0) or 0),
            shares=str(data.get("shares", "0") or "0"),
            last_price=str(data.get("last_price", "0") or "0"),
            side=str(data.get("side", "")),
            fee=str(data.get("fee", "0") or "0"),
        )


@dataclass
class ProfitLossEntry:
    count: int = 0
    amount: float = 0.0


@dataclass
class ProfitLossDetails:
    split: ProfitLossEntry = field(default_factory=ProfitLossEntry)
    buy: ProfitLossEntry = field(default_factory=ProfitLossEntry)
    merge: ProfitLossEntry = field(default_factory=ProfitLossEntry)
    sell: ProfitLossEntry = field(default_factory=ProfitLossEntry)


@dataclass
class ProfitLossSummary:
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    total_fees: float = 0.0
    profit_loss: float = 0.0
    details: ProfitLossDetails = field(default_factory=ProfitLossDetails)
    trade_count: int = 0
    success_count: int = 0
    failed_count: int = 0


def _string_or_number(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _camelize(name: str) -> str:
    parts = name.split("_")
    if not parts:
        return name
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _get_field(data: Dict[str, Any], name: str) -> Any:
    if name in data:
        return data[name]
    camel_name = _camelize(name)
    if camel_name in data:
        return data[camel_name]
    return None


@dataclass
class TopicInfo:
    topic_id: int
    title: str
    status: str
    chain_id: str
    question_id: str
    yes_token: str
    no_token: Optional[str]
    yes_price: Optional[str]
    no_price: Optional[str]
    volume: Optional[str]
    total_price: Optional[str]
    cutoff_time: Optional[str]
    raw: Dict[str, Any]


@dataclass
class CachedTopic:
    topic_id: int
    title: str
    timestamp: int
    data: TopicInfo

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "timestamp": self.timestamp,
            "data": asdict(self.data),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CachedTopic":
        topic_data = data.get("data", {})
        info = TopicInfo(
            topic_id=int(topic_data.get("topic_id")),
            title=str(topic_data.get("title")),
            status=str(topic_data.get("status")),
            chain_id=str(topic_data.get("chain_id")),
            question_id=str(topic_data.get("question_id")),
            yes_token=str(topic_data.get("yes_token")),
            no_token=topic_data.get("no_token"),
            yes_price=topic_data.get("yes_price"),
            no_price=topic_data.get("no_price"),
            volume=topic_data.get("volume"),
            total_price=topic_data.get("total_price"),
            cutoff_time=topic_data.get("cutoff_time"),
            raw=topic_data.get("raw", {}),
        )
        return CachedTopic(
            topic_id=int(data.get("topic_id")),
            title=str(data.get("title")),
            timestamp=int(data.get("timestamp")),
            data=info,
        )


@dataclass
class CachedTopicSummary:
    topic_id: int
    title: str
    timestamp: datetime
    age_minutes: int


def parse_topic_info(payload: Dict[str, Any]) -> TopicInfo:
    result = payload.get("result") or {}
    data = result.get("data") or {}

    topic_id_value = _get_field(data, "topic_id")
    title_value = _get_field(data, "title")
    question_id_value = _get_field(data, "question_id")

    if topic_id_value is None or title_value is None or question_id_value is None:
        raise ValueError("invalid topic response")

    status_value = _string_or_number(_get_field(data, "status")) or "Unknown"
    chain_id_value = _string_or_number(_get_field(data, "chain_id")) or "56"
    yes_token_value = _string_or_number(_get_field(data, "yes_pos")) or ""
    no_token = _string_or_number(_get_field(data, "no_pos"))

    return TopicInfo(
        topic_id=int(topic_id_value),
        title=str(title_value),
        status=status_value,
        chain_id=chain_id_value,
        question_id=_string_or_number(question_id_value) or "",
        yes_token=yes_token_value,
        no_token=no_token,
        yes_price=_string_or_number(_get_field(data, "yes_market_price")),
        no_price=_string_or_number(_get_field(data, "no_market_price")),
        volume=_string_or_number(_get_field(data, "volume")),
        total_price=_string_or_number(_get_field(data, "total_price")),
        cutoff_time=_string_or_number(_get_field(data, "cutoff_time")),
        raw=data,
    )


__all__ = [
    "SubmitOrderPayload",
    "OrderData",
    "SubmitOrderResult",
    "SubmitOrderResponse",
    "CancelOrderResult",
    "CancelOrderResponse",
    "TradeRecord",
    "ProfitLossEntry",
    "ProfitLossDetails",
    "ProfitLossSummary",
    "TopicInfo",
    "CachedTopic",
    "CachedTopicSummary",
    "parse_topic_info",
]