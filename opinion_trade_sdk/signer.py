"""EIP-712 order creation and signing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from eth_account.messages import encode_structured_data
from eth_account.signers.local import LocalAccount

from .constants import CHAIN_ID, EXCHANGE_ADDRESS, SignatureType, Side, ZERO_ADDRESS
from .errors import ParseError, SignerError
from .utils import generate_salt, normalize_address


@dataclass
class OrderParams:
    maker: str
    signer: str
    token_id: str
    maker_amount: str
    taker_amount: str
    side: Side
    expiration: Optional[str]
    fee_rate_bps: Optional[str]


@dataclass
class OrderData:
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
    side: int
    signature_type: int


@dataclass
class SignedOrder(OrderData):
    signature: str


def create_order(params: OrderParams) -> OrderData:
    salt = generate_salt()
    maker = normalize_address(params.maker)
    signer = normalize_address(params.signer)
    taker = ZERO_ADDRESS
    expiration = params.expiration or "0"
    fee_rate_bps = params.fee_rate_bps or "0"

    return OrderData(
        salt=salt,
        maker=maker,
        signer=signer,
        taker=taker,
        token_id=params.token_id,
        maker_amount=params.maker_amount,
        taker_amount=params.taker_amount,
        expiration=expiration,
        nonce="0",
        fee_rate_bps=fee_rate_bps,
        side=int(params.side),
        signature_type=int(SignatureType.POLY_GNOSIS_SAFE),
    )


def _parse_int(value: str) -> int:
    try:
        if value.lower().startswith("0x"):
            return int(value, 16)
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ParseError(f"invalid integer value '{value}'") from exc


def _build_typed_data(order: OrderData) -> dict:
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Order": [
                {"name": "salt", "type": "uint256"},
                {"name": "maker", "type": "address"},
                {"name": "signer", "type": "address"},
                {"name": "taker", "type": "address"},
                {"name": "tokenId", "type": "uint256"},
                {"name": "makerAmount", "type": "uint256"},
                {"name": "takerAmount", "type": "uint256"},
                {"name": "expiration", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "feeRateBps", "type": "uint256"},
                {"name": "side", "type": "uint8"},
                {"name": "signatureType", "type": "uint8"},
            ],
        },
        "primaryType": "Order",
        "domain": {
            "name": "OPINION CTF Exchange",
            "version": "1",
            "chainId": CHAIN_ID,
            "verifyingContract": EXCHANGE_ADDRESS,
        },
        "message": {
            "salt": _parse_int(order.salt),
            "maker": order.maker,
            "signer": order.signer,
            "taker": order.taker,
            "tokenId": _parse_int(order.token_id),
            "makerAmount": _parse_int(order.maker_amount),
            "takerAmount": _parse_int(order.taker_amount),
            "expiration": _parse_int(order.expiration),
            "nonce": _parse_int(order.nonce),
            "feeRateBps": _parse_int(order.fee_rate_bps),
            "side": order.side,
            "signatureType": order.signature_type,
        },
    }


def sign_order(account: LocalAccount, order: OrderData) -> str:
    try:
        typed_data = _build_typed_data(order)
        signable = encode_structured_data(typed_data)
        signed = account.sign_message(signable)
    except Exception as exc:  # pragma: no cover - propagation guard
        raise SignerError(str(exc)) from exc

    signature = signed.signature.hex()
    if not signature.startswith("0x"):
        signature = f"0x{signature}"
    return signature


def build_signed_order(account: LocalAccount, params: OrderParams) -> SignedOrder:
    order = create_order(params)
    signature = sign_order(account, order)
    return SignedOrder(
        **order.__dict__,
        signature=signature,
    )


__all__ = [
    "OrderParams",
    "OrderData",
    "SignedOrder",
    "create_order",
    "build_signed_order",
    "sign_order",
]