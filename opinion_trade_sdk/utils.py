"""Utility helpers shared across the SDK implementation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN, getcontext, localcontext
from typing import Optional, Tuple

from eth_utils import is_hex_address

from .constants import COLLATERAL_TOKEN_DECIMAL, Side, VolumeType
from .errors import InvalidConfigError, ParseError


getcontext().prec = 100


@dataclass
class OrderAmountInput:
    side: Side
    shares: str
    limit_price: str
    volume_type: VolumeType
    buy_input_val: Optional[str]
    is_stable_coin: bool


@dataclass
class OrderAmounts:
    maker_amount: str
    taker_amount: str


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ParseError(f"invalid decimal value '{value}'") from exc


def _quantize_to_int(value: Decimal) -> int:
    with localcontext() as ctx:
        ctx.prec = 100
        quantized = value.to_integral_value(rounding=ROUND_DOWN)
    return int(quantized)


def to_wei(amount: str, decimals: Optional[int] = None) -> str:
    decimals = decimals if decimals is not None else COLLATERAL_TOKEN_DECIMAL
    scale = Decimal(10) ** decimals
    value = _decimal(amount)
    integer = _quantize_to_int(value * scale)
    return str(integer)


def from_wei(amount: str, decimals: Optional[int] = None) -> str:
    decimals = decimals if decimals is not None else COLLATERAL_TOKEN_DECIMAL
    with localcontext() as ctx:
        ctx.prec = 100
        value = Decimal(int(amount)) / (Decimal(10) ** decimals)
        normalized = value.normalize()
        s = format(normalized, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def generate_salt() -> str:
    return str(int(time.time() * 1000))


def get_current_timestamp() -> int:
    return int(time.time())


def _parse_decimal(value: str) -> Tuple[int, int]:
    trimmed = value.strip()
    if not trimmed:
        return 0, 0

    negative = trimmed.startswith("-")
    unsigned = trimmed.lstrip("+-")
    if "." in unsigned:
        integer_part, decimal_part = unsigned.split(".", 1)
    else:
        integer_part, decimal_part = unsigned, ""

    digits = (integer_part + decimal_part) or "0"
    try:
        bigint = int(digits)
    except ValueError as exc:
        raise ParseError(f"invalid decimal value '{value}'") from exc

    if negative:
        bigint = -bigint

    return bigint, len(decimal_part)


def calculate_amount_with_bigint(shares: str, price: str) -> str:
    shares_bigint, shares_scale = _parse_decimal(shares)
    price_bigint, price_scale = _parse_decimal(price)

    total_scale = shares_scale + price_scale

    product = shares_bigint * price_bigint
    scaling_factor = 10 ** 18
    divisor = 100 * (10 ** total_scale)
    if divisor == 0:
        raise ParseError("division by zero")

    result_scaled = (product * scaling_factor) // divisor
    negative = result_scaled < 0
    digits = str(abs(result_scaled))
    if len(digits) > 18:
        int_part = digits[:-18]
        dec_part = digits[-18:]
    else:
        dec_part = digits.rjust(18, "0")
        int_part = "0"

    dec_part = dec_part.rstrip("0")
    if dec_part:
        result = f"{int_part}.{dec_part}"
    else:
        result = int_part

    if negative and result != "0":
        result = f"-{result}"
    return result


def calculate_order_amounts(input_data: OrderAmountInput) -> OrderAmounts:
    if input_data.is_stable_coin:
        price_for_calc = input_data.limit_price
    else:
        price_value = _decimal(input_data.limit_price)
        scaled_price = (price_value * Decimal(100)).normalize()
        price_for_calc = format(scaled_price, "f").rstrip("0").rstrip(".")
        if not price_for_calc:
            price_for_calc = "0"

    if input_data.volume_type is VolumeType.SHARES:
        amount = calculate_amount_with_bigint(input_data.shares, price_for_calc)
    else:
        if not input_data.buy_input_val:
            raise InvalidConfigError(
                "buy_input_val is required when volume_type is Amount"
            )
        amount = input_data.buy_input_val

    if input_data.side is Side.BUY:
        maker_amount = to_wei(amount)
        taker_amount = to_wei(input_data.shares)
    else:
        maker_amount = to_wei(input_data.shares)
        taker_amount = to_wei(amount)

    return OrderAmounts(maker_amount=maker_amount, taker_amount=taker_amount)


def encode_gnosis_safe_signature(signer: str, signature: str) -> str:
    sig = signature.lower().removeprefix("0x")
    addr = normalize_address(signer)
    addr_no_prefix = addr.removeprefix("0x")
    return f"0x{addr_no_prefix}{sig}"


def is_valid_address(address: str) -> bool:
    normalized = address if address.startswith("0x") else f"0x{address}"
    return is_hex_address(normalized)


def normalize_address(address: str) -> str:
    if not address:
        raise ParseError("invalid address: empty string")
    addr = address.strip()
    if not addr.startswith("0x"):
        addr = f"0x{addr}"
    if not is_hex_address(addr):
        raise ParseError(f"invalid address: {address}")
    return addr.lower()


__all__ = [
    "OrderAmountInput",
    "OrderAmounts",
    "to_wei",
    "from_wei",
    "generate_salt",
    "get_current_timestamp",
    "calculate_amount_with_bigint",
    "calculate_order_amounts",
    "encode_gnosis_safe_signature",
    "is_valid_address",
    "normalize_address",
]