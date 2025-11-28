# Mender SDK for Python

A production-level Python SDK for interacting with the [Mender](https://mender.io) IoT OTA update platform.

## Features

- **Async/await support** - Built on top of `httpx` for high-performance async HTTP requests
- **Full type hints** - Complete type annotations for better IDE support and code quality
- **Automatic retries** - Configurable retry logic with exponential backoff for transient failures
- **Comprehensive error handling** - Detailed exception hierarchy for different error scenarios
- **Pagination support** - Easy iteration over paginated API results

## Installation

```bash
pip install mender-sdk
```

## Quick Start

```python
import asyncio
from mender_sdk import MenderClient

async def main():
    async with MenderClient(
        base_url="https://hosted.mender.io",
        token="your-jwt-token",
    ) as client:
        # List all devices
        devices = await client.inventory.list_devices()
        for device in devices.items:
            print(f"Device: {device.id}")

        # Create a deployment
        deployment_id = await client.deployments.create_deployment_for_group(
            name="Production Update v1.0",
            artifact_name="my-artifact",
            group="production",
        )
        print(f"Created deployment: {deployment_id}")

asyncio.run(main())
```

## API Reference

### Inventory Client

```python
# List devices with pagination
devices = await client.inventory.list_devices(page=1, per_page=50)

# Get a specific device
device = await client.inventory.get_device("device-id")

# Get device attribute
ip = device.get_attribute_value("ip_address")

# Update device attributes
from mender_sdk.models.inventory import DeviceAttribute, AttributeScope

await client.inventory.update_device_attributes(
    "device-id",
    [DeviceAttribute(name="location", value="Building A", scope=AttributeScope.INVENTORY)]
)

# Search devices
from mender_sdk.models.inventory import DeviceSearchFilter, FilterDefinition, FilterPredicate

filter_def = FilterDefinition()
filter_def.add(FilterPredicate.equals("device_type", "raspberrypi4"))

search = DeviceSearchFilter(filters=[filter_def])
result = await client.inventory.search_devices(search)

# Iterate over all devices (handles pagination automatically)
async for device in client.inventory.iter_devices():
    print(device.id)

# Group operations
await client.inventory.add_device_to_group("device-id", "production")
groups = await client.inventory.list_groups()
```

### Deployments Client

```python
# List deployments
deployments = await client.deployments.list_deployments()

# Create deployment for specific devices
deployment_id = await client.deployments.create_deployment_for_devices(
    name="Update",
    artifact_name="app-v1.0",
    device_ids=["device-001", "device-002"],
)

# Create deployment for a group
deployment_id = await client.deployments.create_deployment_for_group(
    name="Production Update",
    artifact_name="app-v1.0",
    group="production",
    retries=3,
)

# Get deployment status
deployment = await client.deployments.get_deployment(deployment_id)
stats = await client.deployments.get_deployment_statistics(deployment_id)
print(f"Success: {stats.success}, Failure: {stats.failure}")

# Abort a deployment
await client.deployments.abort_deployment(deployment_id)

# Upload an artifact
artifact_id = await client.deployments.upload_artifact(
    "/path/to/artifact.mender",
    description="Application release v1.0",
)

# List artifacts
artifacts = await client.deployments.list_artifacts()

# List releases
releases = await client.deployments.list_releases()
```

## Error Handling

The SDK provides a comprehensive exception hierarchy:

```python
from mender_sdk import (
    MenderError,              # Base exception
    MenderAPIError,           # API error with status code
    MenderAuthenticationError,# 401 Unauthorized
    MenderNotFoundError,      # 404 Not Found
    MenderValidationError,    # 400 Bad Request
    MenderRateLimitError,     # 429 Too Many Requests
    MenderConnectionError,    # Connection failed
)

try:
    device = await client.inventory.get_device("nonexistent")
except MenderNotFoundError as e:
    print(f"Device not found: {e.message}")
except MenderAuthenticationError:
    print("Invalid or expired token")
except MenderAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Configuration

### Retry Configuration

```python
from mender_sdk import MenderClient
from mender_sdk.utils import RetryConfig

retry_config = RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)

client = MenderClient(
    base_url="https://hosted.mender.io",
    token="your-token",
    retry_config=retry_config,
)
```

### Custom Timeout

```python
client = MenderClient(
    base_url="https://hosted.mender.io",
    token="your-token",
    timeout=60.0,  # seconds
)
```

### SSL Verification

```python
client = MenderClient(
    base_url="https://your-mender-server.com",
    token="your-token",
    verify_ssl=False,  # Disable SSL verification (not recommended for production)
)
```

## Development

### Setup

```bash
git clone https://github.com/your-org/mender-sdk-python.git
cd mender-sdk-python
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Linter

```bash
ruff check src tests
ruff format src tests
```

### Type Checking

```bash
mypy src
```

## License

Apache License 2.0
