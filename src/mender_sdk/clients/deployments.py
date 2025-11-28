"""
Deployments API client for Mender SDK.

Provides methods for managing deployments, artifacts, and releases.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, BinaryIO

from mender_sdk.clients.base import BaseClient
from mender_sdk.models.common import PaginatedResponse, SortOrder
from mender_sdk.models.deployments import (
    Artifact,
    ArtifactUpdate,
    Deployment,
    DeploymentDevice,
    DeploymentStatistics,
    DeploymentStatus,
    DeviceDeploymentStatus,
    NewDeployment,
    Release,
)

logger = logging.getLogger(__name__)


class DeploymentsClient(BaseClient):
    """
    Client for Mender Deployments Management API.

    Provides methods for:
    - Creating and managing deployments
    - Uploading and managing artifacts
    - Managing releases
    - Monitoring deployment status and logs
    """

    BASE_PATH = "/api/management/v1/deployments"

    # -------------------------------------------------------------------------
    # Deployment Operations
    # -------------------------------------------------------------------------

    async def list_deployments(
        self,
        page: int = 1,
        per_page: int = 20,
        status: DeploymentStatus | None = None,
        search: str | None = None,
        sort_by: str = "created",
        sort_order: SortOrder = SortOrder.DESC,
        created_before: str | None = None,
        created_after: str | None = None,
    ) -> PaginatedResponse[Deployment]:
        """
        List deployments with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            status: Filter by deployment status.
            search: Search string for deployment name.
            sort_by: Field to sort by (created, name, etc.).
            sort_order: Sort order (asc/desc).
            created_before: Filter deployments created before this date.
            created_after: Filter deployments created after this date.

        Returns:
            Paginated response containing deployments.
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "sort": f"{sort_by}:{sort_order.value}",
        }

        if status:
            params["status"] = status.value

        if search:
            params["search"] = search

        if created_before:
            params["created_before"] = created_before

        if created_after:
            params["created_after"] = created_after

        response = await self._http.get(
            self._build_path("deployments"),
            params=params,
        )

        deployments = [Deployment.from_dict(d) for d in response.json()]

        return PaginatedResponse.from_response(
            items=deployments,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def iter_deployments(
        self,
        per_page: int = 100,
        **kwargs: Any,
    ) -> AsyncIterator[Deployment]:
        """
        Iterate over all deployments with automatic pagination.

        Args:
            per_page: Number of items per page.
            **kwargs: Additional arguments passed to list_deployments.

        Yields:
            Deployment objects.
        """
        page = 1
        while True:
            result = await self.list_deployments(
                page=page,
                per_page=per_page,
                **kwargs,
            )

            for deployment in result.items:
                yield deployment

            if not result.has_more or len(result.items) < per_page:
                break

            page += 1

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """
        Get a specific deployment by ID.

        Args:
            deployment_id: Deployment ID.

        Returns:
            Deployment object.
        """
        response = await self._http.get(
            self._build_path("deployments", deployment_id),
        )
        return Deployment.from_dict(response.json())

    async def create_deployment(
        self,
        deployment: NewDeployment,
    ) -> str:
        """
        Create a new deployment.

        Args:
            deployment: New deployment configuration.

        Returns:
            Created deployment ID.
        """
        response = await self._http.post(
            self._build_path("deployments"),
            json_data=deployment.to_dict(),
        )

        # Extract deployment ID from Location header
        location = response.headers.get("Location", "")
        return location.split("/")[-1]

    async def create_deployment_for_devices(
        self,
        name: str,
        artifact_name: str,
        device_ids: list[str],
        retries: int = 0,
        force_installation: bool = False,
    ) -> str:
        """
        Create a deployment targeting specific devices.

        Args:
            name: Deployment name.
            artifact_name: Name of the artifact to deploy.
            device_ids: List of device IDs to target.
            retries: Number of retries for failed deployments.
            force_installation: Force installation even if already installed.

        Returns:
            Created deployment ID.
        """
        deployment = NewDeployment(
            name=name,
            artifact_name=artifact_name,
            devices=device_ids,
            retries=retries,
            force_installation=force_installation if force_installation else None,
        )
        return await self.create_deployment(deployment)

    async def create_deployment_for_group(
        self,
        name: str,
        artifact_name: str,
        group: str,
        retries: int = 0,
        max_devices: int | None = None,
        force_installation: bool = False,
    ) -> str:
        """
        Create a deployment targeting a device group.

        Args:
            name: Deployment name.
            artifact_name: Name of the artifact to deploy.
            group: Target group name.
            retries: Number of retries for failed deployments.
            max_devices: Maximum number of devices to deploy to.
            force_installation: Force installation even if already installed.

        Returns:
            Created deployment ID.
        """
        deployment = NewDeployment(
            name=name,
            artifact_name=artifact_name,
            group=group,
            retries=retries,
            max_devices=max_devices,
            force_installation=force_installation if force_installation else None,
        )
        return await self.create_deployment(deployment)

    async def create_deployment_for_all_devices(
        self,
        name: str,
        artifact_name: str,
        retries: int = 0,
        force_installation: bool = False,
    ) -> str:
        """
        Create a deployment targeting all devices.

        Args:
            name: Deployment name.
            artifact_name: Name of the artifact to deploy.
            retries: Number of retries for failed deployments.
            force_installation: Force installation even if already installed.

        Returns:
            Created deployment ID.
        """
        deployment = NewDeployment(
            name=name,
            artifact_name=artifact_name,
            all_devices=True,
            retries=retries,
            force_installation=force_installation if force_installation else None,
        )
        return await self.create_deployment(deployment)

    async def abort_deployment(self, deployment_id: str) -> None:
        """
        Abort a running deployment.

        Args:
            deployment_id: Deployment ID to abort.
        """
        await self._http.put(
            self._build_path("deployments", deployment_id, "status"),
            json_data={"status": "aborted"},
        )

    # -------------------------------------------------------------------------
    # Deployment Statistics and Devices
    # -------------------------------------------------------------------------

    async def get_deployment_statistics(
        self,
        deployment_id: str,
    ) -> DeploymentStatistics:
        """
        Get statistics for a deployment.

        Args:
            deployment_id: Deployment ID.

        Returns:
            Deployment statistics.
        """
        response = await self._http.get(
            self._build_path("deployments", deployment_id, "statistics"),
        )
        return DeploymentStatistics.from_dict(response.json())

    async def list_deployment_devices(
        self,
        deployment_id: str,
        page: int = 1,
        per_page: int = 20,
        status: DeviceDeploymentStatus | None = None,
    ) -> PaginatedResponse[DeploymentDevice]:
        """
        List devices in a deployment.

        Args:
            deployment_id: Deployment ID.
            page: Page number.
            per_page: Items per page.
            status: Filter by device deployment status.

        Returns:
            Paginated response with deployment devices.
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if status:
            params["status"] = status.value

        response = await self._http.get(
            self._build_path("deployments", deployment_id, "devices"),
            params=params,
        )

        devices = [DeploymentDevice.from_dict(d) for d in response.json()]

        return PaginatedResponse.from_response(
            items=devices,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def get_deployment_device_log(
        self,
        deployment_id: str,
        device_id: str,
    ) -> str:
        """
        Get deployment log for a specific device.

        Args:
            deployment_id: Deployment ID.
            device_id: Device ID.

        Returns:
            Deployment log content.
        """
        response = await self._http.get(
            self._build_path(
                "deployments", deployment_id, "devices", device_id, "log"
            ),
        )
        return response.text

    # -------------------------------------------------------------------------
    # Artifact Operations
    # -------------------------------------------------------------------------

    async def list_artifacts(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[Artifact]:
        """
        List all artifacts.

        Args:
            page: Page number.
            per_page: Items per page.

        Returns:
            Paginated response with artifacts.
        """
        response = await self._http.get(
            self._build_path("artifacts"),
            params={"page": page, "per_page": per_page},
        )

        artifacts = [Artifact.from_dict(a) for a in response.json()]

        return PaginatedResponse.from_response(
            items=artifacts,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def iter_artifacts(
        self,
        per_page: int = 100,
    ) -> AsyncIterator[Artifact]:
        """
        Iterate over all artifacts with automatic pagination.

        Args:
            per_page: Number of items per page.

        Yields:
            Artifact objects.
        """
        page = 1
        while True:
            result = await self.list_artifacts(page=page, per_page=per_page)

            for artifact in result.items:
                yield artifact

            if not result.has_more or len(result.items) < per_page:
                break

            page += 1

    async def get_artifact(self, artifact_id: str) -> Artifact:
        """
        Get a specific artifact by ID.

        Args:
            artifact_id: Artifact ID.

        Returns:
            Artifact object.
        """
        response = await self._http.get(
            self._build_path("artifacts", artifact_id),
        )
        return Artifact.from_dict(response.json())

    async def upload_artifact(
        self,
        file: BinaryIO | Path | str,
        description: str | None = None,
    ) -> str:
        """
        Upload a new artifact.

        Args:
            file: File path or file-like object containing the artifact.
            description: Optional artifact description.

        Returns:
            Created artifact ID.
        """
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            with open(file_path, "rb") as f:
                return await self._upload_artifact_file(
                    f, file_path.name, description
                )
        else:
            filename = getattr(file, "name", "artifact.mender")
            if isinstance(filename, (str, Path)):
                filename = Path(filename).name
            return await self._upload_artifact_file(file, filename, description)

    async def _upload_artifact_file(
        self,
        file: BinaryIO,
        filename: str,
        description: str | None = None,
    ) -> str:
        """Upload artifact file."""
        files = {
            "artifact": (filename, file, "application/octet-stream"),
        }

        data = {}
        if description:
            data["description"] = description

        response = await self._http.post(
            self._build_path("artifacts"),
            files=files,
            data=data if data else None,
        )

        # Extract artifact ID from Location header
        location = response.headers.get("Location", "")
        return location.split("/")[-1]

    async def update_artifact(
        self,
        artifact_id: str,
        update: ArtifactUpdate,
    ) -> None:
        """
        Update artifact metadata.

        Args:
            artifact_id: Artifact ID.
            update: Update data.
        """
        await self._http.put(
            self._build_path("artifacts", artifact_id),
            json_data=update.to_dict(),
        )

    async def delete_artifact(self, artifact_id: str) -> None:
        """
        Delete an artifact.

        Args:
            artifact_id: Artifact ID to delete.
        """
        await self._http.delete(self._build_path("artifacts", artifact_id))

    async def download_artifact(self, artifact_id: str) -> bytes:
        """
        Download artifact binary.

        Args:
            artifact_id: Artifact ID.

        Returns:
            Artifact binary content.
        """
        return await self._http.download(
            self._build_path("artifacts", artifact_id, "download"),
        )

    async def get_artifact_download_url(self, artifact_id: str) -> str:
        """
        Get a presigned URL for artifact download.

        Args:
            artifact_id: Artifact ID.

        Returns:
            Presigned download URL.
        """
        response = await self._http.get(
            self._build_path("artifacts", artifact_id, "download"),
        )
        data = response.json()
        return data.get("uri", "")

    # -------------------------------------------------------------------------
    # Release Operations
    # -------------------------------------------------------------------------

    async def list_releases(
        self,
        page: int = 1,
        per_page: int = 20,
        name: str | None = None,
        device_type: str | None = None,
        update_type: str | None = None,
    ) -> PaginatedResponse[Release]:
        """
        List all releases.

        Args:
            page: Page number.
            per_page: Items per page.
            name: Filter by release name.
            device_type: Filter by compatible device type.
            update_type: Filter by update type.

        Returns:
            Paginated response with releases.
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if name:
            params["name"] = name

        if device_type:
            params["device_type"] = device_type

        if update_type:
            params["update_type"] = update_type

        response = await self._http.get(
            self._build_path("deployments", "releases"),
            params=params,
        )

        releases = [Release.from_dict(r) for r in response.json()]

        return PaginatedResponse.from_response(
            items=releases,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def get_release(self, release_name: str) -> Release:
        """
        Get a specific release by name.

        Args:
            release_name: Release name.

        Returns:
            Release object.
        """
        response = await self._http.get(
            self._build_path("deployments", "releases", release_name),
        )
        return Release.from_dict(response.json())

    async def delete_release(self, release_name: str) -> None:
        """
        Delete a release and all its artifacts.

        Args:
            release_name: Release name to delete.
        """
        await self._http.delete(
            self._build_path("deployments", "releases", release_name),
        )

    # -------------------------------------------------------------------------
    # Deployment Limits and Configuration
    # -------------------------------------------------------------------------

    async def get_deployment_limits(self) -> dict[str, Any]:
        """
        Get deployment limits for the tenant.

        Returns:
            Dictionary with limit information.
        """
        response = await self._http.get(self._build_path("limits", "storage"))
        return response.json()

    async def get_device_deployment_history(
        self,
        device_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[Deployment]:
        """
        Get deployment history for a specific device.

        Args:
            device_id: Device ID.
            page: Page number.
            per_page: Items per page.

        Returns:
            Paginated deployment history.
        """
        response = await self._http.get(
            self._build_path("deployments"),
            params={
                "page": page,
                "per_page": per_page,
                "device_id": device_id,
            },
        )

        deployments = [Deployment.from_dict(d) for d in response.json()]

        return PaginatedResponse.from_response(
            items=deployments,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )
