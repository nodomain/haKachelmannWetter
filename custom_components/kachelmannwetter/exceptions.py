"""Exceptions for KachelmannWetter integration."""
from __future__ import annotations


class KachelmannError(Exception):
    """Base exception for KachelmannWetter errors."""


class InvalidAuth(KachelmannError):
    """Raised when authentication fails (invalid API key)."""


class RateLimitError(KachelmannError):
    """Raised when rate limit is hit.

    Attributes:
        retry_after: seconds to wait before retrying (may be None)
    """

    def __init__(self, message: str = "rate limit", retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
