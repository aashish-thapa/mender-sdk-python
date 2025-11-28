"""Tests for main MenderClient."""

import pytest
import respx
from httpx import Response

from mender_sdk import MenderClient
from mender_sdk.exceptions import (
    MenderAuthenticationError,
    MenderNotFoundError,
    MenderValidationError,
)


@pytest.mark.asyncio
class TestMenderClient:
    """Tests for MenderClient."""

    async def test_client_context_manager(self, base_url: str, auth_token: str):
        """Test client as async context manager."""
        async with MenderClient(
            base_url=base_url,
            token=auth_token,
        ) as client:
            assert client is not None
            assert client.inventory is not None
            assert client.deployments is not None

    async def test_client_close(self, base_url: str, auth_token: str):
        """Test client close."""
        client = MenderClient(base_url=base_url, token=auth_token)
        # Access inventory to initialize HTTP client
        _ = client.inventory
        await client.close()

    async def test_set_token(self, base_url: str):
        """Test setting token after initialization."""
        client = MenderClient(base_url=base_url)
        client.set_token("new-token")
        assert client._token == "new-token"

    async def test_client_repr(self, base_url: str, auth_token: str):
        """Test client string representation."""
        client = MenderClient(base_url=base_url, token=auth_token)
        assert base_url in repr(client)


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling."""

    async def test_authentication_error(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test authentication error (401)."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v2/inventory/devices/device-001"
            ).mock(
                return_value=Response(
                    401,
                    json={"error": "Invalid token"},
                )
            )

            with pytest.raises(MenderAuthenticationError):
                await client.inventory.get_device("device-001")

    async def test_not_found_error(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test not found error (404)."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v2/inventory/devices/nonexistent"
            ).mock(
                return_value=Response(
                    404,
                    json={"error": "Device not found"},
                )
            )

            with pytest.raises(MenderNotFoundError):
                await client.inventory.get_device("nonexistent")

    async def test_validation_error(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test validation error (400)."""
        with respx.mock:
            respx.post(
                f"{base_url}/api/management/v1/deployments/deployments"
            ).mock(
                return_value=Response(
                    400,
                    json={"error": "Invalid deployment configuration"},
                )
            )

            from mender_sdk.models.deployments import NewDeployment

            deployment = NewDeployment(
                name="",
                artifact_name="",
            )

            with pytest.raises(MenderValidationError):
                await client.deployments.create_deployment(deployment)
