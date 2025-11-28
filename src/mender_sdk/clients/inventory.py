"""
Inventory API client for Mender SDK.

Provides methods for managing device inventory, groups, attributes, and filters.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from mender_sdk.clients.base import BaseClient
from mender_sdk.models.common import PaginatedResponse, SortOrder
from mender_sdk.models.inventory import (
    AttributeScope,
    Device,
    DeviceAttribute,
    DeviceSearchFilter,
    FilterDefinition,
    Group,
    InventoryFilter,
    SearchResult,
)

logger = logging.getLogger(__name__)


class InventoryClient(BaseClient):
    """
    Client for Mender Inventory Management API.

    Provides methods for:
    - Listing and searching devices
    - Managing device attributes and tags
    - Managing device groups
    - Creating and managing filters
    """

    BASE_PATH = "/api/management/v2/inventory"

    # -------------------------------------------------------------------------
    # Device Operations
    # -------------------------------------------------------------------------

    async def list_devices(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: str | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        has_group: bool | None = None,
        group: str | None = None,
    ) -> PaginatedResponse[Device]:
        """
        List all devices in inventory.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            sort_by: Attribute to sort by.
            sort_order: Sort order (asc/desc).
            has_group: Filter devices by whether they belong to a group.
            group: Filter devices by group name.

        Returns:
            Paginated response containing devices.
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if sort_by:
            params["sort"] = f"{sort_by}:{sort_order.value}"

        if has_group is not None:
            params["has_group"] = str(has_group).lower()

        if group:
            params["group"] = group

        response = await self._http.get(
            self._build_path("devices"),
            params=params,
        )

        devices = [Device.from_dict(d) for d in response.json()]

        return PaginatedResponse.from_response(
            items=devices,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def iter_devices(
        self,
        per_page: int = 100,
        **kwargs: Any,
    ) -> AsyncIterator[Device]:
        """
        Iterate over all devices with automatic pagination.

        Args:
            per_page: Number of items per page.
            **kwargs: Additional arguments passed to list_devices.

        Yields:
            Device objects.
        """
        page = 1
        while True:
            result = await self.list_devices(
                page=page,
                per_page=per_page,
                **kwargs,
            )

            for device in result.items:
                yield device

            if not result.has_more or len(result.items) < per_page:
                break

            page += 1

    async def get_device(self, device_id: str) -> Device:
        """
        Get a specific device by ID.

        Args:
            device_id: Device ID.

        Returns:
            Device object.
        """
        response = await self._http.get(
            self._build_path("devices", device_id),
        )
        return Device.from_dict(response.json())

    async def delete_device(self, device_id: str) -> None:
        """
        Delete a device from inventory.

        Args:
            device_id: Device ID to delete.
        """
        await self._http.delete(self._build_path("devices", device_id))

    # -------------------------------------------------------------------------
    # Device Attributes
    # -------------------------------------------------------------------------

    async def get_device_attributes(
        self,
        device_id: str,
    ) -> list[DeviceAttribute]:
        """
        Get attributes for a device.

        Args:
            device_id: Device ID.

        Returns:
            List of device attributes.
        """
        device = await self.get_device(device_id)
        return device.attributes

    async def update_device_attributes(
        self,
        device_id: str,
        attributes: list[DeviceAttribute],
    ) -> None:
        """
        Update device attributes.

        Args:
            device_id: Device ID.
            attributes: List of attributes to set.
        """
        attrs_data = [attr.to_dict() for attr in attributes]

        await self._http.patch(
            self._build_path("devices", device_id, "attributes"),
            json_data=attrs_data,
        )

    async def set_device_attribute(
        self,
        device_id: str,
        name: str,
        value: Any,
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> None:
        """
        Set a single device attribute.

        Args:
            device_id: Device ID.
            name: Attribute name.
            value: Attribute value.
            scope: Attribute scope.
        """
        await self.update_device_attributes(
            device_id,
            [DeviceAttribute(name=name, value=value, scope=scope)],
        )

    # -------------------------------------------------------------------------
    # Device Tags
    # -------------------------------------------------------------------------

    async def get_device_tags(self, device_id: str) -> list[DeviceAttribute]:
        """
        Get tags for a device.

        Args:
            device_id: Device ID.

        Returns:
            List of tag attributes.
        """
        device = await self.get_device(device_id)
        return [
            attr for attr in device.attributes
            if attr.scope == AttributeScope.TAGS
        ]

    async def set_device_tags(
        self,
        device_id: str,
        tags: dict[str, Any],
    ) -> None:
        """
        Set tags for a device.

        Args:
            device_id: Device ID.
            tags: Dictionary of tag names and values.
        """
        attrs = [
            DeviceAttribute(name=name, value=value, scope=AttributeScope.TAGS)
            for name, value in tags.items()
        ]
        await self.update_device_attributes(device_id, attrs)

    # -------------------------------------------------------------------------
    # Group Operations
    # -------------------------------------------------------------------------

    async def list_groups(self, status: str | None = None) -> list[Group]:
        """
        List all device groups.

        Args:
            status: Filter groups by device status.

        Returns:
            List of groups.
        """
        params = {}
        if status:
            params["status"] = status

        response = await self._http.get(
            self._build_path("groups"),
            params=params if params else None,
        )

        data = response.json()

        # Handle different response formats
        if isinstance(data, list):
            return [Group.from_dict(g) for g in data]

        # Some API versions return {"groups": [...]}
        groups_data = data.get("groups", [])
        return [Group.from_dict(g) for g in groups_data]

    async def get_group_devices(
        self,
        group_name: str,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[str]:
        """
        Get device IDs in a group.

        Args:
            group_name: Group name.
            page: Page number.
            per_page: Items per page.

        Returns:
            Paginated response with device IDs.
        """
        response = await self._http.get(
            self._build_path("groups", group_name, "devices"),
            params={"page": page, "per_page": per_page},
        )

        device_ids = response.json()

        return PaginatedResponse.from_response(
            items=device_ids,
            headers=dict(response.headers),
            page=page,
            per_page=per_page,
        )

    async def get_device_group(self, device_id: str) -> str | None:
        """
        Get the group a device belongs to.

        Args:
            device_id: Device ID.

        Returns:
            Group name or None if device is not in a group.
        """
        response = await self._http.get(
            self._build_path("devices", device_id, "group"),
        )

        data = response.json()
        return data.get("group")

    async def add_device_to_group(
        self,
        device_id: str,
        group_name: str,
    ) -> None:
        """
        Add a device to a group.

        Args:
            device_id: Device ID.
            group_name: Group name to add device to.
        """
        await self._http.put(
            self._build_path("devices", device_id, "group"),
            json_data={"group": group_name},
        )

    async def remove_device_from_group(
        self,
        device_id: str,
        group_name: str,
    ) -> None:
        """
        Remove a device from a group.

        Args:
            device_id: Device ID.
            group_name: Group name to remove device from.
        """
        await self._http.delete(
            self._build_path("groups", group_name, "devices", device_id),
        )

    async def clear_device_group(self, device_id: str) -> None:
        """
        Remove device from its current group.

        Args:
            device_id: Device ID.
        """
        await self._http.delete(
            self._build_path("devices", device_id, "group"),
        )

    async def add_devices_to_group(
        self,
        group_name: str,
        device_ids: list[str],
    ) -> None:
        """
        Add multiple devices to a group.

        Args:
            group_name: Group name.
            device_ids: List of device IDs to add.
        """
        await self._http.patch(
            self._build_path("groups", group_name, "devices"),
            json_data=device_ids,
        )

    async def delete_group(self, group_name: str) -> None:
        """
        Delete a group (removes all devices from group).

        Args:
            group_name: Group name to delete.
        """
        await self._http.delete(self._build_path("groups", group_name))

    # -------------------------------------------------------------------------
    # Search and Filters
    # -------------------------------------------------------------------------

    async def search_devices(
        self,
        search_filter: DeviceSearchFilter,
    ) -> SearchResult:
        """
        Search devices using filter criteria.

        Args:
            search_filter: Search filter configuration.

        Returns:
            Search result containing matching devices.
        """
        response = await self._http.post(
            self._build_path("filters", "search"),
            json_data=search_filter.to_dict(),
        )

        data = response.json()
        total_count = None

        if "X-Total-Count" in response.headers:
            try:
                total_count = int(response.headers["X-Total-Count"])
            except ValueError:
                pass

        return SearchResult.from_response(data, total_count)

    async def search_by_attribute(
        self,
        attribute: str,
        value: Any,
        scope: AttributeScope = AttributeScope.INVENTORY,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResult:
        """
        Search devices by a single attribute value.

        Args:
            attribute: Attribute name.
            value: Value to search for.
            scope: Attribute scope.
            page: Page number.
            per_page: Items per page.

        Returns:
            Search result.
        """
        from mender_sdk.models.inventory import FilterPredicate

        filter_def = FilterDefinition()
        filter_def.add(FilterPredicate.equals(attribute, value, scope))

        search_filter = DeviceSearchFilter(
            filters=[filter_def],
            page=page,
            per_page=per_page,
        )

        return await self.search_devices(search_filter)

    async def list_filters(self) -> list[InventoryFilter]:
        """
        List saved inventory filters.

        Returns:
            List of saved filters.
        """
        response = await self._http.get(self._build_path("filters"))
        return [InventoryFilter.from_dict(f) for f in response.json()]

    async def get_filter(self, filter_id: str) -> InventoryFilter:
        """
        Get a specific saved filter.

        Args:
            filter_id: Filter ID.

        Returns:
            Filter object.
        """
        response = await self._http.get(
            self._build_path("filters", filter_id),
        )
        return InventoryFilter.from_dict(response.json())

    async def create_filter(
        self,
        name: str,
        terms: list[FilterDefinition],
    ) -> str:
        """
        Create a new saved filter.

        Args:
            name: Filter name.
            terms: Filter terms/definitions.

        Returns:
            Created filter ID.
        """
        response = await self._http.post(
            self._build_path("filters"),
            json_data={
                "name": name,
                "terms": [t.to_dict() for t in terms],
            },
        )

        # Extract filter ID from Location header
        location = response.headers.get("Location", "")
        return location.split("/")[-1]

    async def delete_filter(self, filter_id: str) -> None:
        """
        Delete a saved filter.

        Args:
            filter_id: Filter ID to delete.
        """
        await self._http.delete(self._build_path("filters", filter_id))

    # -------------------------------------------------------------------------
    # Filterable Attributes
    # -------------------------------------------------------------------------

    async def get_filterable_attributes(self) -> list[dict[str, Any]]:
        """
        Get list of attributes that can be used in filters.

        Returns:
            List of filterable attribute definitions.
        """
        response = await self._http.get(self._build_path("filters", "attributes"))
        return response.json()
