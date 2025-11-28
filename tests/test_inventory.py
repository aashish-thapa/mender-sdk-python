"""Tests for Inventory API client."""

import pytest
import respx
from httpx import Response

from mender_sdk import MenderClient
from mender_sdk.models.inventory import (
    AttributeScope,
    DeviceAttribute,
    DeviceSearchFilter,
    FilterDefinition,
    FilterPredicate,
)


@pytest.mark.asyncio
class TestInventoryClient:
    """Tests for InventoryClient."""

    async def test_list_devices(
        self,
        client: MenderClient,
        base_url: str,
        sample_device: dict,
    ):
        """Test listing devices."""
        with respx.mock:
            respx.get(f"{base_url}/api/management/v2/inventory/devices").mock(
                return_value=Response(
                    200,
                    json=[sample_device],
                    headers={"X-Total-Count": "1"},
                )
            )

            result = await client.inventory.list_devices()

            assert len(result.items) == 1
            assert result.items[0].id == "device-001"
            assert result.total_count == 1

    async def test_get_device(
        self,
        client: MenderClient,
        base_url: str,
        sample_device: dict,
    ):
        """Test getting a single device."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v2/inventory/devices/device-001"
            ).mock(return_value=Response(200, json=sample_device))

            device = await client.inventory.get_device("device-001")

            assert device.id == "device-001"
            assert len(device.attributes) == 3

    async def test_get_device_attribute_value(
        self,
        client: MenderClient,
        base_url: str,
        sample_device: dict,
    ):
        """Test getting device attribute value."""
        with respx.mock:
            respx.get(
                f"{base_url}/api/management/v2/inventory/devices/device-001"
            ).mock(return_value=Response(200, json=sample_device))

            device = await client.inventory.get_device("device-001")

            assert device.get_attribute_value("ip_address") == "192.168.1.100"
            assert device.get_attribute_value("nonexistent", default="N/A") == "N/A"

    async def test_update_device_attributes(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test updating device attributes."""
        with respx.mock:
            route = respx.patch(
                f"{base_url}/api/management/v2/inventory/devices/device-001/attributes"
            ).mock(return_value=Response(200))

            attributes = [
                DeviceAttribute(
                    name="location",
                    value="Building A",
                    scope=AttributeScope.INVENTORY,
                ),
            ]

            await client.inventory.update_device_attributes(
                "device-001",
                attributes,
            )

            assert route.called

    async def test_list_groups(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test listing groups."""
        with respx.mock:
            respx.get(f"{base_url}/api/management/v2/inventory/groups").mock(
                return_value=Response(
                    200,
                    json=[
                        {"name": "production", "device_count": 50},
                        {"name": "staging", "device_count": 10},
                    ],
                )
            )

            groups = await client.inventory.list_groups()

            assert len(groups) == 2
            assert groups[0].name == "production"
            assert groups[0].device_count == 50

    async def test_add_device_to_group(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test adding device to group."""
        with respx.mock:
            route = respx.put(
                f"{base_url}/api/management/v2/inventory/devices/device-001/group"
            ).mock(return_value=Response(204))

            await client.inventory.add_device_to_group("device-001", "production")

            assert route.called

    async def test_search_devices(
        self,
        client: MenderClient,
        base_url: str,
        sample_device: dict,
    ):
        """Test searching devices."""
        with respx.mock:
            respx.post(
                f"{base_url}/api/management/v2/inventory/filters/search"
            ).mock(
                return_value=Response(
                    200,
                    json=[sample_device],
                    headers={"X-Total-Count": "1"},
                )
            )

            filter_def = FilterDefinition()
            filter_def.add(
                FilterPredicate.equals("device_type", "raspberrypi4")
            )

            search_filter = DeviceSearchFilter(filters=[filter_def])
            result = await client.inventory.search_devices(search_filter)

            assert len(result.devices) == 1
            assert result.total_count == 1

    async def test_search_by_attribute(
        self,
        client: MenderClient,
        base_url: str,
        sample_device: dict,
    ):
        """Test convenience search by attribute."""
        with respx.mock:
            respx.post(
                f"{base_url}/api/management/v2/inventory/filters/search"
            ).mock(
                return_value=Response(
                    200,
                    json=[sample_device],
                    headers={"X-Total-Count": "1"},
                )
            )

            result = await client.inventory.search_by_attribute(
                "device_type",
                "raspberrypi4",
            )

            assert len(result.devices) == 1

    async def test_delete_device(
        self,
        client: MenderClient,
        base_url: str,
    ):
        """Test deleting device."""
        with respx.mock:
            route = respx.delete(
                f"{base_url}/api/management/v2/inventory/devices/device-001"
            ).mock(return_value=Response(204))

            await client.inventory.delete_device("device-001")

            assert route.called
