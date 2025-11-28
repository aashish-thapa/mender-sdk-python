"""
Mender SDK for Python.

A production-level Python SDK for interacting with the Mender IoT OTA update platform.
"""

from mender_sdk.client import MenderClient
from mender_sdk.exceptions import (
    MenderError,
    MenderAPIError,
    MenderAuthenticationError,
    MenderNotFoundError,
    MenderValidationError,
    MenderRateLimitError,
    MenderConnectionError,
)

__version__ = "1.0.0"
__all__ = [
    "MenderClient",
    "MenderError",
    "MenderAPIError",
    "MenderAuthenticationError",
    "MenderNotFoundError",
    "MenderValidationError",
    "MenderRateLimitError",
    "MenderConnectionError",
]
