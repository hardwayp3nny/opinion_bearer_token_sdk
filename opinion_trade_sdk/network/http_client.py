"""HTTP client wrapper with Opinion Trade specific defaults."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ..errors import (
    ApiError,
    HttpStatusError,
    InvalidConfigError,
    NetworkError,
    ParseError,
    SdkError,
)
from .performance import NetworkPerformance, default_monitor

DEFAULT_TIMEOUT = 10.0


@dataclass
class HttpClientConfig:
    timeout: Optional[float] = None
    headers: Optional[Dict[str, str]] = None
    monitor: Optional[NetworkPerformance] = None


@dataclass
class RequestOptions:
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None
    check_api_error: bool = True


class HttpClient:
    def __init__(self, config: Optional[HttpClientConfig] = None) -> None:
        config = config or HttpClientConfig()

        timeout = config.timeout if config.timeout is not None else DEFAULT_TIMEOUT

        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://app.opinion.trade/",
            "Origin": "https://app.opinion.trade",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        }

        if config.headers:
            default_headers.update(config.headers)

        try:
            self._client = httpx.AsyncClient(
                headers=default_headers,
                timeout=timeout,
                trust_env=True,
            )
        except Exception as exc:  # pragma: no cover - protective guard
            raise InvalidConfigError(str(exc)) from exc

        self._monitor = config.monitor or default_monitor()
        self._default_timeout = timeout

    async def request(
        self,
        method: str,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Any:
        options = options or RequestOptions()
        self._monitor.record_request(url)

        timeout = options.timeout if options.timeout is not None else self._default_timeout

        headers = {}
        if options.headers:
            headers.update(options.headers)

        request_kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers or None,
            "timeout": timeout,
        }

        if options.data is not None:
            request_kwargs["json"] = options.data

        try:
            response = await self._client.request(**request_kwargs)
        except httpx.TimeoutException as exc:
            raise NetworkError(str(exc)) from exc
        except httpx.TransportError as exc:
            raise SdkError(f"http error: {exc}") from exc

        if response.status_code // 100 != 2:
            try:
                body = response.text
            except Exception:  # pragma: no cover - defensive
                body = None
            raise HttpStatusError(response.status_code, response.reason_phrase, body)

        try:
            payload = response.json()
        except ValueError as exc:
            raise ParseError(f"failed to decode json response: {exc}") from exc

        if options.check_api_error and isinstance(payload, dict):
            errno = _parse_errno(payload.get("errno"))
            if errno != 0:
                message = str(payload.get("errmsg") or payload.get("message") or "Unknown API error")
                raise ApiError(errno, message)

        return payload

    async def get(self, url: str, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("GET", url, options)

    async def post(self, url: str, data: Any, options: Optional[RequestOptions] = None) -> Any:
        options = options or RequestOptions()
        options.data = data
        return await self.request("POST", url, options)

    async def put(self, url: str, data: Any, options: Optional[RequestOptions] = None) -> Any:
        options = options or RequestOptions()
        options.data = data
        return await self.request("PUT", url, options)

    async def delete(self, url: str, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("DELETE", url, options)

    @property
    def default_timeout(self) -> float:
        return self._default_timeout

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "HttpClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # pragma: no cover - context helper
        await self.aclose()


_DEFAULT_CLIENT: HttpClient | None = None


def default_client() -> HttpClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = HttpClient()
    return _DEFAULT_CLIENT


def _parse_errno(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


__all__ = [
    "HttpClient",
    "HttpClientConfig",
    "RequestOptions",
    "ApiError",
    "NetworkError",
    "default_client",
]