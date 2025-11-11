"""Demo placing an order using the Python SDK.

Required environment variables:
- PRIVATE_KEY: hex-encoded private key (0x...)
- MAKER_ADDRESS: maker (Gnosis Safe) address
- AUTHORIZATION_TOKEN: Bearer token from the web app
- TOPIC_ID: numeric topic identifier
- LIMIT_PRICE: 0-100 string (e.g. "50" for 0.50 USDT)
- SHARES: number of shares to trade (string)

Optional:
- POSITION: "YES" or "NO" (default: YES)
- SIDE: "BUY" or "SELL" (default: BUY)
- SAFE_RATE: optional API safe rate (default: "0")
- API_BASE_URL, COLLATERAL_TOKEN, CHAIN_ID, CACHE_DIR
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from opinion_trade_sdk import (
    CancelOrderParams,
    CreateLimitOrderByTopicParams,
    OpinionTradeSdk,
    OpinionTradeSdkConfig,
    OrderPosition,
    Side,
    VolumeType,
)


def env_var(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise RuntimeError(f"Environment variable {key} is required")
    return value


async def main() -> None:
    load_dotenv()

    private_key = env_var("PRIVATE_KEY")
    maker_address = env_var("MAKER_ADDRESS")
    authorization_token = env_var("AUTHORIZATION_TOKEN")

    topic_id = int(env_var("TOPIC_ID"))
    limit_price = env_var("LIMIT_PRICE")
    shares = env_var("SHARES")

    position = os.environ.get("POSITION", "YES").upper()
    side_env = os.environ.get("SIDE", "BUY").upper()
    safe_rate = os.environ.get("SAFE_RATE")

    try:
        side = Side.BUY if side_env == "BUY" else Side.SELL
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Unsupported SIDE value: {side_env}") from exc

    if position == "YES":
        order_position = OrderPosition.YES
    elif position == "NO":
        order_position = OrderPosition.NO
    else:
        raise RuntimeError(f"Unsupported POSITION value: {position}")

    config = OpinionTradeSdkConfig(
        private_key=private_key,
        maker_address=maker_address,
        authorization_token=authorization_token,
        collateral_token_addr=os.environ.get("COLLATERAL_TOKEN"),
        chain_id=int(os.environ["CHAIN_ID"]) if os.environ.get("CHAIN_ID") else None,
        api_base_url=os.environ.get("API_BASE_URL"),
        cache_dir=Path(os.environ["CACHE_DIR"]) if os.environ.get("CACHE_DIR") else None,
    )

    sdk = OpinionTradeSdk(config)

    try:
        topic_info = await sdk.get_topic_info(topic_id, False)
        print(f"Fetched topic info: {topic_info.title} ({topic_info.topic_id})")
        print(f"YES token: {topic_info.yes_token}")
        print(f"NO token: {topic_info.no_token}")

        response = await sdk.create_order_by_topic(
            CreateLimitOrderByTopicParams(
                topic_id=topic_id,
                position=order_position,
                limit_price=limit_price,
                shares=shares,
                side=side,
                volume_type=VolumeType.SHARES,
                buy_input_val=None,
                is_stable_coin=True,
                safe_rate=safe_rate or "0",
            )
        )

        print("Order submission response:")
        print(f"errno: {response.errno}")
        if response.errmsg:
            print(f"errmsg: {response.errmsg}")

        order_data = response.result.order_data
        if order_data is None:
            print("No order data returned.")
        else:
            print(
                f"order_id: {order_data.order_id}, trans_no: {order_data.trans_no}, "
                f"status: {order_data.status}, side: {order_data.side}, "
                f"price: {order_data.price}, filled: {order_data.filled}"
            )
            print(
                f"topic_id: {order_data.topic_id}, topic_title: {order_data.topic_title}, "
                f"chain_id: {order_data.chain_id}"
            )

            if order_data.trans_no:
                print("Waiting 0.5 seconds before cancelling order...")
                await asyncio.sleep(0.1)
                cancel_response = await sdk.cancel_order(
                    CancelOrderParams(trans_no=order_data.trans_no, chain_id=None)
                )
                print("Cancel order response:")
                print(f"errno: {cancel_response.errno}")
                if cancel_response.errmsg:
                    print(f"errmsg: {cancel_response.errmsg}")
                print(f"success: {cancel_response.result.success}")
    finally:
        await sdk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
