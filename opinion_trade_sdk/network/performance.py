"""Simple in-memory network performance tracker."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Deque


DEFAULT_WINDOW_MILLIS = 10_000
DEFAULT_TARGET_DOMAIN = "proxy.opinion.trade"


@dataclass
class NetworkPerformance:
    window_millis: int = DEFAULT_WINDOW_MILLIS
    target_domain: str = DEFAULT_TARGET_DOMAIN

    def __post_init__(self) -> None:
        self._timestamps: Deque[float] = deque()
        self._lock = Lock()

    def record_request(self, url: str) -> None:
        if self.target_domain not in url:
            return
        now = monotonic()
        with self._lock:
            self._timestamps.append(now)
            self._cleanup_locked(now)

    def get_qps(self) -> float:
        now = monotonic()
        with self._lock:
            self._cleanup_locked(now)
            if not self._timestamps:
                return 0.0
            oldest = self._timestamps[0]
            elapsed = max(now - oldest, 1e-9)
            qps = len(self._timestamps) / elapsed
        return round(qps, 2)

    def get_request_count(self) -> int:
        now = monotonic()
        with self._lock:
            self._cleanup_locked(now)
            return len(self._timestamps)

    def reset(self) -> None:
        with self._lock:
            self._timestamps.clear()

    def _cleanup_locked(self, now: float) -> None:
        window_seconds = self.window_millis / 1000.0
        while self._timestamps and now - self._timestamps[0] > window_seconds:
            self._timestamps.popleft()


_DEFAULT_MONITOR: NetworkPerformance | None = None


def default_monitor() -> NetworkPerformance:
    global _DEFAULT_MONITOR
    if _DEFAULT_MONITOR is None:
        _DEFAULT_MONITOR = NetworkPerformance()
    return _DEFAULT_MONITOR


__all__ = ["NetworkPerformance", "default_monitor"]