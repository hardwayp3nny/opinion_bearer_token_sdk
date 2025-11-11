"""Topic metadata helpers with caching support."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import aiofiles

from .errors import ParseError
from .network.http_client import RequestOptions, default_client
from .types import CachedTopic, CachedTopicSummary, TopicInfo, parse_topic_info

DEFAULT_CACHE_RELATIVE = ".cache/topics"


@dataclass
class OrderBookTokens:
    yes: str
    no: Optional[str]


@dataclass
class OrderBookConfig:
    question_id: str
    tokens: OrderBookTokens
    chain_id: str
    title: str


class TopicApi:
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.base_url = "https://proxy.opinion.trade:8443/api/bsc/api/v2/topic"
        self.cache_dir = cache_dir or default_cache_directory()

    async def ensure_cache_dir(self) -> None:
        await asyncio.to_thread(self.cache_dir.mkdir, parents=True, exist_ok=True)

    def cache_path(self, topic_id: int) -> Path:
        return self.cache_dir / f"topic_{topic_id}.json"

    async def load_from_cache(self, topic_id: int) -> Optional[TopicInfo]:
        path = self.cache_path(topic_id)
        if not path.exists():
            return None

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as fh:
                content = await fh.read()
            data = json.loads(content)
            cached = CachedTopic.from_dict(data)
        except Exception:
            return None

        age = int(datetime.now(timezone.utc).timestamp() * 1000) - cached.timestamp
        max_age = 24 * 60 * 60 * 1000
        if age <= max_age:
            return cached.data
        return None

    async def save_to_cache(self, topic_id: int, info: TopicInfo) -> None:
        await self.ensure_cache_dir()
        cached = CachedTopic(
            topic_id=topic_id,
            title=info.title,
            timestamp=int(datetime.now(timezone.utc).timestamp() * 1000),
            data=info,
        )
        path = self.cache_path(topic_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as fh:
            await fh.write(json.dumps(cached.to_dict(), ensure_ascii=False, indent=2))

    async def get_topic_info(self, topic_id: int, force_refresh: bool) -> TopicInfo:
        if not force_refresh:
            cached = await self.load_from_cache(topic_id)
            if cached is not None:
                return cached

        url = f"{self.base_url}/{topic_id}"
        response = await default_client().get(url, RequestOptions())
        try:
            info = parse_topic_info(response)
        except Exception as exc:
            raise ParseError(str(exc)) from exc
        await self.save_to_cache(topic_id, info)
        return info

    async def get_order_book_config(self, topic_id: int) -> OrderBookConfig:
        info = await self.get_topic_info(topic_id, False)
        return OrderBookConfig(
            question_id=info.question_id,
            tokens=OrderBookTokens(yes=info.yes_token, no=info.no_token),
            chain_id=info.chain_id,
            title=info.title,
        )

    async def clear_cache(self, topic_id: int) -> None:
        path = self.cache_path(topic_id)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def clear_all_cache(self) -> None:
        if not self.cache_dir.exists():
            return
        for entry in await asyncio.to_thread(list, self.cache_dir.glob("topic_*.json")):
            await asyncio.to_thread(entry.unlink)

    async def list_cached_topics(self) -> List[CachedTopicSummary]:
        if not self.cache_dir.exists():
            return []

        summaries: List[CachedTopicSummary] = []
        for path in await asyncio.to_thread(list, self.cache_dir.glob("topic_*.json")):
            try:
                async with aiofiles.open(path, "r", encoding="utf-8") as fh:
                    content = await fh.read()
                data = json.loads(content)
                cached = CachedTopic.from_dict(data)
                timestamp = datetime.fromtimestamp(
                    cached.timestamp / 1000, tz=timezone.utc
                )
                age_minutes = int(
                    (datetime.now(timezone.utc) - timestamp).total_seconds() // 60
                )
                summaries.append(
                    CachedTopicSummary(
                        topic_id=cached.topic_id,
                        title=cached.title,
                        timestamp=timestamp,
                        age_minutes=age_minutes,
                    )
                )
            except Exception:
                continue

        return summaries


def default_cache_directory() -> Path:
    return Path.cwd() / DEFAULT_CACHE_RELATIVE


__all__ = [
    "TopicApi",
    "OrderBookConfig",
    "OrderBookTokens",
    "CachedTopicSummary",
    "TopicInfo",
]
