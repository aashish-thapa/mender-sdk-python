"""
Retry utilities for handling transient failures.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from mender_sdk.exceptions import (
    MenderConnectionError,
    MenderRateLimitError,
    MenderServerError,
    MenderTimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            MenderConnectionError,
            MenderTimeoutError,
            MenderServerError,
            MenderRateLimitError,
        )
    )

    def calculate_delay(self, attempt: int, retry_after: int | None = None) -> float:
        """Calculate delay for a given attempt number."""
        if retry_after is not None:
            return float(retry_after)

        delay = min(
            self.base_delay * (self.exponential_base**attempt),
            self.max_delay,
        )

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay


def retry_with_backoff(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        config: Retry configuration. Uses defaults if not provided.

    Returns:
        Decorated function with retry logic.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt >= config.max_retries:
                        logger.warning(
                            "Max retries (%d) exceeded for %s",
                            config.max_retries,
                            func.__name__,
                        )
                        raise

                    retry_after = None
                    if isinstance(e, MenderRateLimitError):
                        retry_after = e.retry_after

                    delay = config.calculate_delay(attempt, retry_after)

                    logger.info(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.2fs",
                        attempt + 1,
                        config.max_retries + 1,
                        func.__name__,
                        str(e),
                        delay,
                    )

                    await asyncio.sleep(delay)

            # This should not be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator
