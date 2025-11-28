"""Tests for Deployments API client."""

import pytest
import respx
from httpx import Response

from mender_sdk import MenderClient
from mender_sdk.models.deployments import (
    DeploymentStatus,
    DeviceDeploymentStatus,
    NewDeployment,
)


@pytest.mark.asyncio
class TestDeploymentsClient:
    """Tests for DeploymentsClient."""

    async def test_list_deployments(
        self,
        client: MenderClient,
        base_url: str,
        sample_deployment: dict,
    ):
        """Test listing deployments."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/deployments"
            ).mock(
                return_value=Response(
                    200,
                    json=[sample_deployment],
                    headers={"X-Total-Count": "1"},
                )
            )

            result = await client.deployments.list_deployments()

            assert len(result.items) == 1
            assert result.items[0].id == "deployment-001"
            assert result.items[0].status == DeploymentStatus.INPROGRESS

    async def test_get_deployment(
        self,
        client: MenderClient,
        base_url: str,
        sample_deployment: dict,
    ):
        """Test getting a single deployment."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/deployments/deployment-001"
            ).mock(return_value=Response(200, json=sample_deployment))

            deployment = await client.deployments.get_deployment("deployment-001")

            assert deployment.id == "deployment-001"
            assert deployment.name == "Production Update v1.0"
            assert deployment.device_count == 100

    async def test_create_deployment(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test creating a deployment."""
        with respx.mock:
            respx.post(
                f"{base_url}/api/management/v1/deployments/deployments"
            ).mock(
                return_value=Response(
                    201,
                    headers={"Location": "/deployments/new-deployment-001"},
                )
            )

            deployment = NewDeployment(
                name="Test Deployment",
                artifact_name="app-release-1.0",
                devices=["device-001", "device-002"],
            )

            deployment_id = await client.deployments.create_deployment(deployment)

            assert deployment_id == "new-deployment-001"

    async def test_create_deployment_for_group(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test creating deployment for a group."""
        with respx.mock:
            respx.post(
                f"{base_url}/api/management/v1/deployments/deployments"
            ).mock(
                return_value=Response(
                    201,
                    headers={"Location": "/deployments/group-deployment-001"},
                )
            )

            deployment_id = await client.deployments.create_deployment_for_group(
                name="Group Deployment",
                artifact_name="app-release-1.0",
                group="production",
                retries=3,
            )

            assert deployment_id == "group-deployment-001"

    async def test_abort_deployment(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test aborting a deployment."""
        with respx.mock:
            route = respx.put(
                f"{base_url}/api/management/v1/deployments/deployments/deployment-001/status"
            ).mock(return_value=Response(204))

            await client.deployments.abort_deployment("deployment-001")

            assert route.called

    async def test_get_deployment_statistics(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test getting deployment statistics."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/deployments/deployment-001/statistics"
            ).mock(
                return_value=Response(
                    200,
                    json={
                        "status": "inprogress",
                        "success": 45,
                        "pending": 30,
                        "downloading": 10,
                        "installing": 10,
                        "failure": 5,
                    },
                )
            )

            stats = await client.deployments.get_deployment_statistics(
                "deployment-001"
            )

            assert stats.success == 45
            assert stats.pending == 30
            assert stats.failure == 5
            assert stats.total == 100

    async def test_list_deployment_devices(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test listing devices in a deployment."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/deployments/deployment-001/devices"
            ).mock(
                return_value=Response(
                    200,
                    json=[
                        {
                            "id": "device-001",
                            "status": "success",
                            "created": "2024-01-20T10:00:00Z",
                            "finished": "2024-01-20T10:30:00Z",
                        },
                        {
                            "id": "device-002",
                            "status": "installing",
                            "created": "2024-01-20T10:00:00Z",
                        },
                    ],
                )
            )

            result = await client.deployments.list_deployment_devices(
                "deployment-001"
            )

            assert len(result.items) == 2
            assert result.items[0].status == DeviceDeploymentStatus.SUCCESS
            assert result.items[1].status == DeviceDeploymentStatus.INSTALLING

    async def test_list_artifacts(
        self,
        client: MenderClient,
        base_url: str,
        sample_artifact: dict,
    ):
        """Test listing artifacts."""
        with respx.mock:
            respx.get(f"{base_url}/api/management/v1/deployments/artifacts").mock(
                return_value=Response(200, json=[sample_artifact])
            )

            result = await client.deployments.list_artifacts()

            assert len(result.items) == 1
            assert result.items[0].name == "app-release-1.0"
            assert result.items[0].signed is True

    async def test_get_artifact(
        self,
        client: MenderClient,
        base_url: str,
        sample_artifact: dict,
    ):
        """Test getting a single artifact."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/artifacts/artifact-001"
            ).mock(return_value=Response(200, json=sample_artifact))

            artifact = await client.deployments.get_artifact("artifact-001")

            assert artifact.id == "artifact-001"
            assert artifact.size == 52428800
            assert "raspberrypi4" in artifact.device_types_compatible

    async def test_delete_artifact(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test deleting an artifact."""
        with respx.mock:
            route = respx.delete(
                f"{base_url}/api/management/v1/deployments/artifacts/artifact-001"
            ).mock(return_value=Response(204))

            await client.deployments.delete_artifact("artifact-001")

            assert route.called

    async def test_list_releases(
        self,
        client: MenderClient,
        base_url: str,
        sample_artifact: dict,
    ):
        """Test listing releases."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v1/deployments/deployments/releases"
            ).mock(
                return_value=Response(
                    200,
                    json=[
                        {
                            "name": "release-1.0",
                            "artifacts": [sample_artifact],
                            "device_types": ["raspberrypi4"],
                        }
                    ],
                )
            )

            result = await client.deployments.list_releases()

            assert len(result.items) == 1
            assert result.items[0].name == "release-1.0"
            assert len(result.items[0].artifacts) == 1
