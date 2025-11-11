"""Custom error hierarchy mirroring the Rust SDK error types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class SdkError(Exception):
    """Base exception for all SDK failures."""


class InvalidConfigError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"invalid configuration: {message}")


class MissingFieldError(SdkError):
    def __init__(self, field: str) -> None:
        super().__init__(f"missing field: {field}")


class ParseError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"parse error: {message}")


class SignerError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"signer error: {message}")


class NetworkError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"network error: {message}")


class HttpStatusError(SdkError):
    def __init__(self, status: int, message: str, body: Optional[str]) -> None:
        suffix = f": {body}" if body else ""
        super().__init__(f"http {status}: {message}{suffix}")
        self.status = status
        self.message = message
        self.body = body


class ApiError(SdkError):
    def __init__(self, errno: int, message: str) -> None:
        super().__init__(f"api error (errno: {errno}): {message}")
        self.errno = errno
        self.message = message


class HttpError(SdkError):
    """Wrapper used internally when httpx raises an exception."""


class IoError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"io error: {message}")


class JsonError(SdkError):
    def __init__(self, message: str) -> None:
        super().__init__(f"json error: {message}")


@dataclass
class HttpBody:
    content: Optional[str]

    def __str__(self) -> str:
        if not self.content:
            return ""
        return f": {self.content}"


__all__ = [
    "SdkError",
    "InvalidConfigError",
    "MissingFieldError",
    "ParseError",
    "SignerError",
    "NetworkError",
    "HttpStatusError",
    "ApiError",
    "HttpError",
    "IoError",
    "JsonError",
    "HttpBody",
]