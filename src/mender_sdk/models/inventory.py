"""
Data models for Mender Inventory API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FilterOperator(str, Enum):
    """Filter operators for search queries."""

    EQUAL = "$eq"
    NOT_EQUAL = "$ne"
    IN = "$in"
    NOT_IN = "$nin"
    EXISTS = "$exists"
    REGEX = "$regex"
    GREATER_THAN = "$gt"
    GREATER_THAN_OR_EQUAL = "$gte"
    LESS_THAN = "$lt"
    LESS_THAN_OR_EQUAL = "$lte"


class AttributeScope(str, Enum):
    """Scope of device attributes."""

    IDENTITY = "identity"
    INVENTORY = "inventory"
    SYSTEM = "system"
    TAGS = "tags"


@dataclass
class DeviceAttribute:
    """Device attribute with name, value, and scope."""

    name: str
    value: Any
    scope: AttributeScope = AttributeScope.INVENTORY
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result = {
            "name": self.name,
            "value": self.value,
            "scope": self.scope.value,
        }
        if self.description:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceAttribute:
        """Create from API response dictionary."""
        return cls(
            name=data["name"],
            value=data.get("value"),
            scope=AttributeScope(data.get("scope", "inventory")),
            description=data.get("description"),
        )


@dataclass
class Device:
    """Device representation."""

    id: str
    attributes: list[DeviceAttribute] = field(default_factory=list)
    created_ts: datetime | None = None
    updated_ts: datetime | None = None
    check_in_time: datetime | None = None

    def get_attribute(
        self,
        name: str,
        scope: AttributeScope | None = None,
    ) -> DeviceAttribute | None:
        """Get attribute by name and optional scope."""
        for attr in self.attributes:
            if attr.name == name:
                if scope is None or attr.scope == scope:
                    return attr
        return None

    def get_attribute_value(
        self,
        name: str,
        scope: AttributeScope | None = None,
        default: Any = None,
    ) -> Any:
        """Get attribute value by name."""
        attr = self.get_attribute(name, scope)
        return attr.value if attr else default

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        """Create from API response dictionary."""
        attributes = [
            DeviceAttribute.from_dict(attr)
            for attr in data.get("attributes", [])
        ]

        return cls(
            id=data["id"],
            attributes=attributes,
            created_ts=cls._parse_datetime(data.get("created_ts")),
            updated_ts=cls._parse_datetime(data.get("updated_ts")),
            check_in_time=cls._parse_datetime(data.get("check_in_time")),
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse ISO datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


@dataclass
class DeviceInventory:
    """Extended device inventory information."""

    device: Device
    group: str | None = None
    status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceInventory:
        """Create from API response dictionary."""
        return cls(
            device=Device.from_dict(data),
            group=data.get("group"),
            status=data.get("status"),
        )


@dataclass
class Group:
    """Device group."""

    name: str
    device_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Group:
        """Create from API response dictionary."""
        if isinstance(data, str):
            return cls(name=data)
        return cls(
            name=data["name"],
            device_count=data.get("device_count", 0),
        )


@dataclass
class DeviceGroup:
    """Device group assignment."""

    device_id: str
    group: str


@dataclass
class FilterPredicate:
    """Single filter predicate for search queries."""

    attribute: str
    scope: AttributeScope
    type: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "attribute": self.attribute,
            "scope": self.scope.value,
            "type": self.type,
            "value": self.value,
        }

    @classmethod
    def equals(
        cls,
        attribute: str,
        value: Any,
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> FilterPredicate:
        """Create an equals filter."""
        return cls(attribute, scope, "$eq", value)

    @classmethod
    def not_equals(
        cls,
        attribute: str,
        value: Any,
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> FilterPredicate:
        """Create a not equals filter."""
        return cls(attribute, scope, "$ne", value)

    @classmethod
    def contains(
        cls,
        attribute: str,
        value: str,
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> FilterPredicate:
        """Create a regex filter for contains."""
        return cls(attribute, scope, "$regex", f".*{value}.*")

    @classmethod
    def exists(
        cls,
        attribute: str,
        exists: bool = True,
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> FilterPredicate:
        """Create an exists filter."""
        return cls(attribute, scope, "$exists", exists)

    @classmethod
    def in_list(
        cls,
        attribute: str,
        values: list[Any],
        scope: AttributeScope = AttributeScope.INVENTORY,
    ) -> FilterPredicate:
        """Create an in-list filter."""
        return cls(attribute, scope, "$in", values)


@dataclass
class FilterDefinition:
    """Filter definition with multiple predicates."""

    predicates: list[FilterPredicate] = field(default_factory=list)

    def to_dict(self) -> list[dict[str, Any]]:
        """Convert to list of predicate dictionaries."""
        return [p.to_dict() for p in self.predicates]

    def add(self, predicate: FilterPredicate) -> FilterDefinition:
        """Add a predicate to the filter."""
        self.predicates.append(predicate)
        return self


@dataclass
class DeviceSearchFilter:
    """Search filter for querying devices."""

    filters: list[FilterDefinition] = field(default_factory=list)
    sort: list[dict[str, str]] = field(default_factory=list)
    page: int = 1
    per_page: int = 20

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {
            "page": self.page,
            "per_page": self.per_page,
        }

        if self.filters:
            result["filters"] = [f.to_dict() for f in self.filters]

        if self.sort:
            result["sort"] = self.sort

        return result

    def add_filter(self, filter_def: FilterDefinition) -> DeviceSearchFilter:
        """Add a filter definition."""
        self.filters.append(filter_def)
        return self

    def add_sort(
        self,
        attribute: str,
        scope: AttributeScope = AttributeScope.INVENTORY,
        order: str = "asc",
    ) -> DeviceSearchFilter:
        """Add a sort criterion."""
        self.sort.append({
            "attribute": attribute,
            "scope": scope.value,
            "order": order,
        })
        return self


@dataclass
class InventoryFilter:
    """Saved inventory filter."""

    id: str
    name: str
    terms: list[FilterDefinition] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InventoryFilter:
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            terms=[],  # Simplified; real implementation would parse terms
        )


@dataclass
class SearchResult:
    """Search result containing devices."""

    devices: list[Device]
    total_count: int | None = None

    @classmethod
    def from_response(
        cls,
        data: list[dict[str, Any]],
        total_count: int | None = None,
    ) -> SearchResult:
        """Create from API response."""
        return cls(
            devices=[Device.from_dict(d) for d in data],
            total_count=total_count,
        )
