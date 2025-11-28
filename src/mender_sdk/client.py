"""
Main Mender SDK client.

Provides a unified interface to all Mender APIs.
"""

from __future__ import annotations

import logging
from typing import Any

from mender_sdk.clients.deployments import DeploymentsClient
from mender_sdk.clients.inventory import InventoryClient
from mender_sdk.utils.http import HTTPClient
from mender_sdk.utils.retry import RetryConfig

logger = logging.getLogger(__name__)


class MenderClient:
    """
    Main client for interacting with the Mender API.

    Provides access to all Mender services through specialized sub-clients:
    - inventory: Device inventory management
    - deployments: Deployment and artifact management

    Example:
        ```python
        import asyncio
        from mender_sdk import MenderClient

        async def main():
            async with MenderClient(
                base_url="https://hosted.mender.io",
                token="your-jwt-token",
            ) as client:
                # List devices
                devices = await client.inventory.list_devices()
                for device in devices.items:
                    print(f"Device: {device.id}")

                # Create a deployment
                deployment_id = await client.deployments.create_deployment_for_group(
                    name="Update v1.0",
                    artifact_name="my-artifact",
                    group="production",
                )
                print(f"Created deployment: {deployment_id}")

        asyncio.run(main())
        ```
    """

    DEFAULT_BASE_URL = "https://hosted.mender.io"

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize the Mender client.

        Args:
            base_url: Base URL for the Mender API. Defaults to hosted.mender.io.
            token: JWT authentication token.
            timeout: Request timeout in seconds.
            retry_config: Configuration for retry behavior on transient failures.
            verify_ssl: Whether to verify SSL certificates.
        """
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._token = token
        self._timeout = timeout
        self._retry_config = retry_config
        self._verify_ssl = verify_ssl

        self._http_client: HTTPClient | None = None
        self._inventory: InventoryClient | None = None
        self._deployments: DeploymentsClient | None = None

    def _ensure_http_client(self) -> HTTPClient:
        """Ensure HTTP client is initialized."""
        if self._http_client is None:
            self._http_client = HTTPClient(
                base_url=self._base_url,
                token=self._token,
                timeout=self._timeout,
                retry_config=self._retry_config,
                verify_ssl=self._verify_ssl,
            )
        return self._http_client

    @property
    def inventory(self) -> InventoryClient:
        """
        Get the Inventory API client.

        Returns:
            InventoryClient for device inventory operations.
        """
        if self._inventory is None:
            self._inventory = InventoryClient(self._ensure_http_client())
        return self._inventory

    @property
    def deployments(self) -> DeploymentsClient:
        """
        Get the Deployments API client.

        Returns:
            DeploymentsClient for deployment operations.
        """
        if self._deployments is None:
            self._deployments = DeploymentsClient(self._ensure_http_client())
        return self._deployments

    def set_token(self, token: str) -> None:
        """
        Set or update the authentication token.

        Args:
            token: JWT authentication token.
        """
        self._token = token
        if self._http_client:
            self._http_client.token = token

    async def close(self) -> None:
        """Close the client and release resources."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None
            self._inventory = None
            self._deployments = None

    async def __aenter__(self) -> MenderClient:
        """Enter async context manager."""
        self._ensure_http_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"MenderClient(base_url={self._base_url!r})"


def create_client(
    base_url: str | None = None,
    token: str | None = None,
    **kwargs: Any,
) -> MenderClient:
    """
    Factory function to create a MenderClient instance.

    Args:
        base_url: Base URL for the Mender API.
        token: JWT authentication token.
        **kwargs: Additional arguments passed to MenderClient.

    Returns:
        Configured MenderClient instance.

    Example:
        ```python
        from mender_sdk import create_client

        client = create_client(
            base_url="https://hosted.mender.io",
            token="your-token",
        )
        ```
    """
    return MenderClient(base_url=base_url, token=token, **kwargs)
