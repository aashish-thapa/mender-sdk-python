"""Pytest configuration and fixtures for Mender SDK tests."""

import pytest
import respx
from httpx import Response

from mender_sdk import MenderClient


@pytest.fixture
def base_url() -> str:
    """Base URL for test server."""
    return "https://test.mender.io"


@pytest.fixture
def auth_token() -> str:
    """Test authentication token."""
    return "test-jwt-token"


@pytest.fixture
def mock_api() -> respx.MockRouter:
    """Create a mock API router."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
async def client(base_url: str, auth_token: str) -> MenderClient:
    """Create a test Mender client."""
    async with MenderClient(
        base_url=base_url,
        token=auth_token,
        verify_ssl=False,
    ) as mender_client:
        yield mender_client


@pytest.fixture
def sample_device() -> dict:
    """Sample device data."""
    return {
        "id": "device-001",
        "attributes": [
            {"name": "device_type", "value": "raspberrypi4", "scope": "identity"},
            {"name": "artifact_name", "value": "release-1.0", "scope": "inventory"},
            {"name": "ip_address", "value": "192.168.1.100", "scope": "inventory"},
        ],
        "created_ts": "2024-01-15T10:30:00Z",
        "updated_ts": "2024-01-20T14:45:00Z",
    }


@pytest.fixture
def sample_deployment() -> dict:
    """Sample deployment data."""
    return {
        "id": "deployment-001",
        "name": "Production Update v1.0",
        "artifact_name": "app-release-1.0",
        "created": "2024-01-20T10:00:00Z",
        "status": "inprogress",
        "device_count": 100,
        "statistics": {
            "status": "inprogress",
            "success": 45,
            "pending": 30,
            "downloading": 10,
            "installing": 10,
            "failure": 5,
        },
    }


@pytest.fixture
def sample_artifact() -> dict:
    """Sample artifact data."""
    return {
        "id": "artifact-001",
        "name": "app-release-1.0",
        "description": "Application release version 1.0",
        "device_types_compatible": ["raspberrypi4", "raspberrypi3"],
        "info": {"format": "mender", "version": 3},
        "signed": True,
        "size": 52428800,
        "modified": "2024-01-18T09:00:00Z",
    }
