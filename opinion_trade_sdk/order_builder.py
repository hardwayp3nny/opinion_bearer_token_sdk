"""Order construction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Optional

from .constants import Side, VolumeType
from .errors import InvalidConfigError, ParseError
from .signer import OrderParams, SignedOrder
from .types import SubmitOrderPayload
from .utils import OrderAmountInput, calculate_order_amounts, get_current_timestamp


@dataclass
class BuildOrderParamsInput:
    maker: str
    signer: str
    token_id: str
    limit_price: str
    shares: str
    side: Side
    volume_type: VolumeType
    buy_input_val: Optional[str]
    is_stable_coin: bool
    expiration: Optional[str]
    fee_rate_bps: Optional[str]


@dataclass
class BuildApiPayloadInput:
    signed_order: SignedOrder
    topic_id: int
    limit_price: str
    collateral_token_addr: str
    chain_id: int
    is_stable_coin: bool
    safe_rate: Optional[str]


def build_order_params(input_data: BuildOrderParamsInput) -> OrderParams:
    if not input_data.maker or not input_data.signer:
        raise InvalidConfigError("maker and signer addresses are required")

    if not input_data.token_id:
        raise InvalidConfigError("token_id is required")

    try:
        price_value = Decimal(input_data.limit_price)
    except Exception as exc:
        raise ParseError(f"invalid limit price: {exc}") from exc

    if price_value < 0 or price_value > 100:
        raise InvalidConfigError("limit price must be between 0 and 100")

    amount_input = OrderAmountInput(
        side=input_data.side,
        shares=input_data.shares,
        limit_price=input_data.limit_price,
        volume_type=input_data.volume_type,
        buy_input_val=input_data.buy_input_val,
        is_stable_coin=input_data.is_stable_coin,
    )

    amounts = calculate_order_amounts(amount_input)

    return OrderParams(
        maker=input_data.maker,
        signer=input_data.signer,
        token_id=input_data.token_id,
        maker_amount=amounts.maker_amount,
        taker_amount=amounts.taker_amount,
        side=input_data.side,
        expiration=input_data.expiration,
        fee_rate_bps=input_data.fee_rate_bps,
    )


def build_api_payload(input_data: BuildApiPayloadInput) -> SubmitOrderPayload:
    if input_data.is_stable_coin:
        price = format_price_with_bigint(input_data.limit_price)
    else:
        price = input_data.limit_price

    side = str(input_data.signed_order.side)
    signature_type = str(input_data.signed_order.signature_type)
    timestamp = get_current_timestamp()

    return SubmitOrderPayload(
        topic_id=input_data.topic_id,
        contract_address="",
        price=price,
        trading_method=2,
        salt=input_data.signed_order.salt,
        maker=input_data.signed_order.maker,
        signer=input_data.signed_order.signer,
        taker=input_data.signed_order.taker,
        token_id=input_data.signed_order.token_id,
        maker_amount=input_data.signed_order.maker_amount,
        taker_amount=input_data.signed_order.taker_amount,
        expiration=input_data.signed_order.expiration,
        nonce=input_data.signed_order.nonce,
        fee_rate_bps=input_data.signed_order.fee_rate_bps,
        side=side,
        signature_type=signature_type,
        signature=input_data.signed_order.signature,
        timestamp=timestamp,
        sign=input_data.signed_order.signature,
        safe_rate=input_data.safe_rate or "0",
        order_exp_time=input_data.signed_order.expiration,
        currency_address=input_data.collateral_token_addr,
        chain_id=input_data.chain_id,
    )


def format_price_with_bigint(limit_price: str) -> str:
    trimmed = limit_price.strip()
    if not trimmed:
        raise ParseError("limit price cannot be empty")

    try:
        price_decimal = Decimal(trimmed)
    except (InvalidOperation, ValueError) as exc:
        raise ParseError(f"invalid price '{limit_price}'") from exc

    scaled = (price_decimal * Decimal(10)).quantize(Decimal("1"), rounding=ROUND_DOWN)
    scaled_int = int(scaled)

    integer_part = scaled_int // 1000
    decimal_part = scaled_int % 1000

    return f"{integer_part}.{decimal_part:03d}"


__all__ = [
    "BuildOrderParamsInput",
    "BuildApiPayloadInput",
    "build_order_params",
    "build_api_payload",
    "format_price_with_bigint",
]