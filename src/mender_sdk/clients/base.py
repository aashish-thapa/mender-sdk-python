"""
Base client class for Mender API clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mender_sdk.utils.http import HTTPClient


class BaseClient:
    """Base class for API clients."""

    BASE_PATH: str = ""

    def __init__(self, http_client: HTTPClient) -> None:
        """
        Initialize the client.

        Args:
            http_client: HTTP client instance for making requests.
        """
        self._http = http_client

    def _build_path(self, *parts: str) -> str:
        """Build API path from parts."""
        path = self.BASE_PATH
        for part in parts:
            if part:
                path = f"{path}/{part.strip('/')}"
        return path
