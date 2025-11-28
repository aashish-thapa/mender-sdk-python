"""
Common data models shared across Mender SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class PaginationParams:
    """Parameters for paginated requests."""

    page: int = 1
    per_page: int = 20

    def to_params(self) -> dict[str, int]:
        """Convert to query parameters."""
        return {"page": self.page, "per_page": self.per_page}


@dataclass
class PaginatedResponse(Generic[T]):
    """Response containing paginated data."""

    items: list[T]
    total_count: int | None = None
    page: int = 1
    per_page: int = 20
    has_more: bool = False

    @property
    def total_pages(self) -> int | None:
        """Calculate total number of pages."""
        if self.total_count is None:
            return None
        return (self.total_count + self.per_page - 1) // self.per_page

    @classmethod
    def from_response(
        cls,
        items: list[T],
        headers: dict[str, str],
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[T]:
        """Create from API response with headers."""
        total_count = None
        # Headers are case-insensitive, check both cases
        header_value = headers.get("X-Total-Count") or headers.get("x-total-count")
        if header_value:
            try:
                total_count = int(header_value)
            except ValueError:
                pass

        has_more = len(items) >= per_page

        return cls(
            items=items,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_more=has_more,
        )
