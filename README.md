# Opinion Trade Python SDK（中文说明）

该仓库提供 Opinion.Trade 预测市场的官方 Python SDK，可用于在后端服务或自动化脚本中完成下单、撤单、订单查询、题目缓存等操作。SDK 采用异步设计，能够与 `asyncio` 生态无缝集成。

## 环境要求

- Python 3.9 及以上版本
- 已安装 `pip`，并可访问 Python 软件源
- 拥有有效的链上私钥、Maker 地址以及 Opinion.Trade 授权 Token

## 安装

在项目根目录执行：

```bash
pip install -e .
```

或直接在其他项目中通过 `pip` 引入源码路径：

```bash
pip install git+https://<your-repo-url>
```

安装完成后即可通过 `import opinion_trade_sdk` 使用。

## 快速开始

```python
import asyncio

from opinion_trade_sdk import (
    OpinionTradeSdk,
    OpinionTradeSdkConfig,
    CreateLimitOrderByTopicParams,
    OrderPosition,
    VolumeType,
    Side,
)


async def main() -> None:
    config = OpinionTradeSdkConfig(
        private_key="0x您的私钥",
        maker_address="0x您的Maker地址",
        authorization_token="Bearer <从网页获取的Token>",
    )

    sdk = OpinionTradeSdk(config)

    try:
        topic = await sdk.get_topic_info(topic_id=12345, force_refresh=False)
        print(f"题目：{topic.title}")

        response = await sdk.buy_by_topic(
            CreateLimitOrderByTopicParams(
                topic_id=topic.topic_id,
                position=OrderPosition.YES,
                limit_price="55",
                shares="10",
                side=Side.BUY,
                volume_type=VolumeType.SHARES,
                buy_input_val=None,
                is_stable_coin=True,
                safe_rate="0",
            )
        )

        print("下单返回：", response.errno, response.errmsg)
    finally:
        await sdk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

以上示例中，`limit_price="55"` 表示价格 0.55 USDT，`shares="10"` 表示买入 10 股。

## 核心配置项

`OpinionTradeSdkConfig` 中的字段说明：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `private_key` | 是 | EOA 或 Safe 对应的私钥，用于签名订单 |
| `maker_address` | 是 | Maker（通常为 Gnosis Safe）地址 |
| `authorization_token` | 否 | Web 端获取的 Bearer Token，未提供则仅能访问无需鉴权的接口 |
| `collateral_token_addr` | 否 | 抵押物合约地址，默认使用 USDT (BSC) |
| `chain_id` | 否 | 指定链 ID，默认 56 (BSC) |
| `api_base_url` | 否 | API 网关地址，默认指向官方代理 |
| `cache_dir` | 否 | 题目缓存目录，默认为仓库下 `.cache/topics` |

## 常用接口

### 题目信息与缓存

- `get_topic_info(topic_id, force_refresh)`：获取题目详情，可选择强制刷新；默认使用本地缓存
- `clear_topic_cache(topic_id)` / `clear_topic_cache(None)`：删除单个或全部题目缓存
- `list_cached_topics()`：列出缓存中已有的题目摘要

### 下单接口

- `create_limit_order(params)`：基于 tokenId 下限价单
- `buy(params)` / `sell(params)`：便捷的买入或卖出方法
- `create_order_by_topic(params)`：根据题目 ID 自动解析 YES/NO token 下单
- `buy_by_topic(params)` / `sell_by_topic(params)`：结合题目 ID 的便捷买/卖接口

所有下单接口都返回 `SubmitOrderResponse`，其中 `result.order_data` 包含链上订单详情。

### 查询与统计

- `query_orders(params)` / `get_open_orders(params)` / `get_closed_orders(params)`：按地址分页查询订单
- `query_trades(params)` / `get_all_trades(params)`：查询成交记录，可自动分页
- `calculate_profit_loss(trades)`：基于成交列表计算盈亏汇总
- `get_profit_loss(params)`：整合查询成交与盈亏计算的高阶方法

### 撤单

- `cancel_order(params)`：提交订单撤销请求（需要 `trans_no` 和 `chain_id`）

### 订单簿

通过 `TopicApi.get_order_book_config(topic_id)` 获取题目配置，再实例化 `OrderBookApi`：

```python
from opinion_trade_sdk import TopicApi
from opinion_trade_sdk.order_book_api import OrderBookApi, OrderBookPosition

config = await sdk.topic_api.get_order_book_config(topic_id)
order_book_api = OrderBookApi(config)
books = await order_book_api.get_both_order_books()
```

返回的 `OrderBook` 包含买卖档位（bids/asks）、最新价和时间戳。

## 示例程序

`examples/place_order.py` 演示了从环境变量读取配置、获取题目信息、下单并撤单的完整流程。可复制 `place_order.env.example` 为 `.env` 后根据实际账号填写变量，再运行：

```bash
python examples/place_order.py
```

## 注意事项

- 所有接口均为异步方法，需在 `asyncio` 事件循环中调用
- 私钥和 Token 属于敏感信息，建议通过环境变量或密钥管理服务提供
- 官方 API 会进行频率限制，遇到 `ApiError` 或 `HttpStatusError` 时请根据错误信息重试或退避
- 在生产环境中使用前，建议先在测试账号或小额资金下验证调用逻辑
