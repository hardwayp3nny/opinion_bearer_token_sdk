"""Primary SDK surface for interacting with Opinion.Trade."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount

from .constants import (
    API_BASE_URL,
    CHAIN_ID,
    COLLATERAL_TOKEN_ADDRESS,
    OrderQueryType,
    Side,
    VolumeType,
)
from .errors import InvalidConfigError, ParseError
from .network.http_client import HttpClient, HttpClientConfig, RequestOptions
from .order_builder import (
    BuildApiPayloadInput,
    BuildOrderParamsInput,
    build_api_payload,
    build_order_params,
)
from .signer import build_signed_order
from .topic_api import CachedTopicSummary, TopicApi
from .types import (
    CancelOrderResponse,
    SubmitOrderResponse,
    ProfitLossDetails,
    ProfitLossSummary,
    SubmitOrderPayload,
    TopicInfo,
    TradeRecord,
    OrderData,
)
from .utils import normalize_address


@dataclass
class OpinionTradeSdkConfig:
    private_key: str
    maker_address: str
    authorization_token: Optional[str] = None
    collateral_token_addr: Optional[str] = None
    chain_id: Optional[int] = None
    api_base_url: Optional[str] = None
    cache_dir: Optional[Path] = None


@dataclass
class CreateLimitOrderParams:
    topic_id: int
    token_id: str
    limit_price: str
    shares: str
    side: Side = Side.BUY
    volume_type: VolumeType = VolumeType.SHARES
    buy_input_val: Optional[str] = None
    is_stable_coin: bool = True
    safe_rate: Optional[str] = "0"


@dataclass
class OrderQueryResult:
    list: List[OrderData]
    total: int


@dataclass
class TradeQueryResult:
    list: List[TradeRecord]
    total: int


class OrderPosition(str, Enum):
    YES = "YES"
    NO = "NO"


@dataclass
class CreateLimitOrderByTopicParams:
    topic_id: int
    position: OrderPosition
    limit_price: str
    shares: str
    side: Side
    volume_type: VolumeType
    buy_input_val: Optional[str]
    is_stable_coin: bool
    safe_rate: Optional[str]


@dataclass
class QueryOrdersParams:
    wallet_address: str = ""
    query_type: OrderQueryType = OrderQueryType.OPEN
    topic_id: Optional[int] = None
    page: int = 1
    limit: int = 10


@dataclass
class QueryTradesParams:
    wallet_address: str = ""
    topic_id: Optional[int] = None
    page: int = 1
    limit: int = 10


@dataclass
class ProfitLossParams:
    topic_id: int
    wallet_address: Optional[str] = None


@dataclass
class CancelOrderParams:
    trans_no: str
    chain_id: Optional[int] = None


class OpinionTradeSdk:
    def __init__(self, config: OpinionTradeSdkConfig) -> None:
        private_key = (config.private_key or "").strip()
        if not private_key:
            raise InvalidConfigError("private key is required")

        try:
            self.wallet: LocalAccount = Account.from_key(private_key)
        except ValueError as exc:
            raise InvalidConfigError(f"invalid private key: {exc}") from exc

        try:
            self.signer_address = normalize_address(self.wallet.address)
        except ParseError as exc:
            raise InvalidConfigError(str(exc)) from exc

        self.maker_address = normalize_address(config.maker_address)

        self.chain_id = config.chain_id if config.chain_id is not None else CHAIN_ID

        collateral_override = (
            normalize_address(config.collateral_token_addr)
            if config.collateral_token_addr
            else None
        )
        self.collateral_token_addr = (
            collateral_override
            if collateral_override is not None
            else COLLATERAL_TOKEN_ADDRESS.lower()
        )

        self.api_base_url = config.api_base_url or API_BASE_URL

        token = config.authorization_token
        if token and not token.startswith("Bearer "):
            token = f"Bearer {token}"
        self.authorization_token = token

        headers = {"Authorization": token} if token else None
        self.http_client = HttpClient(
            HttpClientConfig(headers=headers)
        )
        self.topic_api = TopicApi(config.cache_dir)

    def signer_address_hex(self) -> str:
        return self.signer_address

    def maker_address_hex(self) -> str:
        return self.maker_address

    async def create_limit_order(
        self, params: CreateLimitOrderParams
    ) -> SubmitOrderResponse:
        order_params = build_order_params(
            BuildOrderParamsInput(
                maker=self.maker_address,
                signer=self.signer_address,
                token_id=params.token_id,
                limit_price=params.limit_price,
                shares=params.shares,
                side=params.side,
                volume_type=params.volume_type,
                buy_input_val=params.buy_input_val,
                is_stable_coin=params.is_stable_coin,
                expiration=None,
                fee_rate_bps="0",
            )
        )

        signed_order = build_signed_order(self.wallet, order_params)

        payload = build_api_payload(
            BuildApiPayloadInput(
                signed_order=signed_order,
                topic_id=params.topic_id,
                limit_price=params.limit_price,
                collateral_token_addr=self.collateral_token_addr,
                chain_id=self.chain_id,
                is_stable_coin=params.is_stable_coin,
                safe_rate=params.safe_rate,
            )
        )

        return await self.submit_order(payload)

    async def submit_order(self, payload: SubmitOrderPayload) -> SubmitOrderResponse:
        url = f"{self.api_base_url}/v2/order"
        data = payload.to_dict()
        response = await self.post_json(url, data)
        return SubmitOrderResponse.from_dict(response)

    async def buy(self, params: CreateLimitOrderParams) -> SubmitOrderResponse:
        params.side = Side.BUY
        return await self.create_limit_order(params)

    async def sell(self, params: CreateLimitOrderParams) -> SubmitOrderResponse:
        params.side = Side.SELL
        return await self.create_limit_order(params)

    async def get_topic_info(self, topic_id: int, force_refresh: bool) -> TopicInfo:
        return await self.topic_api.get_topic_info(topic_id, force_refresh)

    async def create_order_by_topic(
        self, params: CreateLimitOrderByTopicParams
    ) -> SubmitOrderResponse:
        info = await self.topic_api.get_topic_info(params.topic_id, False)
        if params.position == OrderPosition.YES:
            token_id = info.yes_token
        else:
            if not info.no_token:
                raise InvalidConfigError("NO token ID not found")
            token_id = info.no_token

        limit_params = CreateLimitOrderParams(
            topic_id=params.topic_id,
            token_id=token_id,
            limit_price=params.limit_price,
            shares=params.shares,
            side=params.side,
            volume_type=params.volume_type,
            buy_input_val=params.buy_input_val,
            is_stable_coin=params.is_stable_coin,
            safe_rate=params.safe_rate,
        )

        return await self.create_limit_order(limit_params)

    async def buy_by_topic(
        self, params: CreateLimitOrderByTopicParams
    ) -> SubmitOrderResponse:
        params.side = Side.BUY
        return await self.create_order_by_topic(params)

    async def sell_by_topic(
        self, params: CreateLimitOrderByTopicParams
    ) -> SubmitOrderResponse:
        params.side = Side.SELL
        return await self.create_order_by_topic(params)

    async def query_orders(self, params: QueryOrdersParams) -> OrderQueryResult:
        if not params.wallet_address:
            raise InvalidConfigError("wallet_address is required")

        url = (
            f"{self.api_base_url}/v2/order?page={params.page}&limit={params.limit}"
            f"&walletAddress={params.wallet_address}&queryType={int(params.query_type)}"
        )
        #query_type: 1: open orders, 2: closed orders
        if params.topic_id is not None:
            url += f"&topicId={params.topic_id}"

        response = await self.get_json(url)
        result = response.get("result", {}) if isinstance(response, dict) else {}
        order_list = result.get("list")
        orders: List[OrderData] = []
        if isinstance(order_list, list):
            for item in order_list:
                if isinstance(item, dict):
                    orders.append(OrderData.from_dict(item))
        total = int(result.get("total", 0)) if isinstance(result, dict) else 0
        return OrderQueryResult(list=orders, total=total)

    async def get_open_orders(self, params: QueryOrdersParams) -> OrderQueryResult:
        if not params.wallet_address:
            params.wallet_address = self.signer_address
        params.query_type = OrderQueryType.OPEN
        return await self.query_orders(params)

    async def get_closed_orders(self, params: QueryOrdersParams) -> OrderQueryResult:
        if not params.wallet_address:
            params.wallet_address = self.signer_address
        params.query_type = OrderQueryType.CLOSED
        return await self.query_orders(params)

    async def query_trades(self, params: QueryTradesParams) -> TradeQueryResult:
        if not params.wallet_address:
            raise InvalidConfigError("wallet_address is required")

        url = (
            f"{self.api_base_url}/v2/trade?page={params.page}&limit={params.limit}"
            f"&walletAddress={params.wallet_address}"
        )
        if params.topic_id is not None:
            url += f"&topicId={params.topic_id}"

        response = await self.get_json(url)
        result = response.get("result", {}) if isinstance(response, dict) else {}
        list_value = result.get("list") if isinstance(result, dict) else None
        trades: List[TradeRecord] = []
        if isinstance(list_value, list):
            for item in list_value:
                if isinstance(item, dict):
                    trades.append(TradeRecord.from_dict(item))
        total = int(result.get("total", 0)) if isinstance(result, dict) else 0
        return TradeQueryResult(list=trades, total=total)

    async def get_all_trades(self, params: QueryTradesParams) -> List[TradeRecord]:
        trades: List[TradeRecord] = []
        page = 1
        while True:
            page_params = QueryTradesParams(
                wallet_address=params.wallet_address,
                topic_id=params.topic_id,
                page=page,
                limit=params.limit,
            )
            result = await self.query_trades(page_params)
            if not result.list:
                break
            trades.extend(result.list)
            if result.total == 0 or len(trades) >= result.total:
                break
            page += 1
        return trades

    def calculate_profit_loss(self, trades: List[TradeRecord]) -> ProfitLossSummary:
        total_inflow = 0.0
        total_outflow = 0.0
        total_fees = 0.0
        success_count = 0
        failed_count = 0

        details = ProfitLossDetails()

        for trade in trades:
            if trade.status != 2:
                failed_count += 1
                continue

            success_count += 1

            shares = float(trade.shares or 0)
            last_price = float(trade.last_price or 0)
            try:
                fee_float = float(trade.fee) / 1e18
            except ValueError:
                fee_float = 0.0
            total_fees += fee_float

            side = trade.side
            if side == "Split":
                amount = shares * 0.5
                total_inflow += amount
                details.split.count += 1
                details.split.amount += amount
            elif side == "Buy":
                amount = shares * last_price
                total_inflow += amount
                details.buy.count += 1
                details.buy.amount += amount
            elif side == "Merge":
                amount = shares * 0.5
                total_outflow += amount
                details.merge.count += 1
                details.merge.amount += amount
            elif side == "Sell":
                amount = shares * last_price
                total_outflow += amount
                details.sell.count += 1
                details.sell.amount += amount

        profit_loss = total_outflow - total_inflow - total_fees

        return ProfitLossSummary(
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            total_fees=total_fees,
            profit_loss=profit_loss,
            details=details,
            trade_count=len(trades),
            success_count=success_count,
            failed_count=failed_count,
        )

    async def get_profit_loss(self, params: ProfitLossParams) -> ProfitLossSummary:
        wallet_address = params.wallet_address or self.signer_address
        trades = await self.get_all_trades(
            QueryTradesParams(
                wallet_address=wallet_address,
                topic_id=params.topic_id,
                page=1,
                limit=200,
            )
        )
        return self.calculate_profit_loss(trades)

    async def cancel_order(self, params: CancelOrderParams) -> CancelOrderResponse:
        if not params.trans_no:
            raise InvalidConfigError("trans_no is required")

        url = f"{self.api_base_url}/v1/order/cancel/order"
        payload = {
            "trans_no": params.trans_no,
            "chainId": params.chain_id if params.chain_id is not None else self.chain_id,
        }
        response = await self.post_json(url, payload)
        return CancelOrderResponse.from_dict(response)

    async def clear_topic_cache(self, topic_id: Optional[int]) -> None:
        if topic_id is not None:
            await self.topic_api.clear_cache(topic_id)
        else:
            await self.topic_api.clear_all_cache()

    async def list_cached_topics(self) -> List[CachedTopicSummary]:
        return await self.topic_api.list_cached_topics()

    async def get_json(self, url: str) -> Dict:
        options = RequestOptions()
        headers = self.auth_headers()
        if headers:
            options.headers = headers
        response = await self.http_client.get(url, options)
        if isinstance(response, dict):
            return response
        raise ParseError("unexpected response format")

    async def post_json(self, url: str, data: Dict) -> Dict:
        options = RequestOptions()
        headers = self.auth_headers()
        if headers:
            options.headers = headers
        response = await self.http_client.post(url, data, options)
        if isinstance(response, dict):
            return response
        raise ParseError("unexpected response format")

    def auth_headers(self) -> Optional[Dict[str, str]]:
        if self.authorization_token:
            return {"Authorization": self.authorization_token}
        return None

    async def aclose(self) -> None:
        await self.http_client.aclose()


__all__ = [
    "OpinionTradeSdk",
    "OpinionTradeSdkConfig",
    "CreateLimitOrderParams",
    "CreateLimitOrderByTopicParams",
    "OrderPosition",
    "OrderQueryResult",
    "TradeQueryResult",
    "QueryOrdersParams",
    "QueryTradesParams",
    "ProfitLossParams",
    "CancelOrderParams",
]
