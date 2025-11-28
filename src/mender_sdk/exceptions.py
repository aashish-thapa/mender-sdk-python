"""
Mender SDK Exceptions.

Custom exception classes for handling Mender API errors.
"""

from __future__ import annotations

from typing import Any


class MenderError(Exception):
    """Base exception for all Mender SDK errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class MenderAPIError(MenderError):
    """Exception raised when Mender API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        details = {
            "status_code": status_code,
            "response_body": response_body,
            "request_id": request_id,
        }
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id


class MenderAuthenticationError(MenderAPIError):
    """Exception raised when authentication fails (401 Unauthorized)."""

    def __init__(
        self,
        message: str = "Authentication failed. Please check your credentials.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 401, response_body, request_id)


class MenderAuthorizationError(MenderAPIError):
    """Exception raised when authorization fails (403 Forbidden)."""

    def __init__(
        self,
        message: str = "Access denied. Insufficient permissions.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 403, response_body, request_id)


class MenderNotFoundError(MenderAPIError):
    """Exception raised when a resource is not found (404 Not Found)."""

    def __init__(
        self,
        message: str = "Resource not found.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 404, response_body, request_id)


class MenderValidationError(MenderAPIError):
    """Exception raised when request validation fails (400 Bad Request)."""

    def __init__(
        self,
        message: str = "Request validation failed.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 400, response_body, request_id)


class MenderConflictError(MenderAPIError):
    """Exception raised when there's a resource conflict (409 Conflict)."""

    def __init__(
        self,
        message: str = "Resource conflict.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 409, response_body, request_id)


class MenderRateLimitError(MenderAPIError):
    """Exception raised when rate limit is exceeded (429 Too Many Requests)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry later.",
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, 429, response_body, request_id)
        self.retry_after = retry_after


class MenderServerError(MenderAPIError):
    """Exception raised for server errors (5xx)."""

    def __init__(
        self,
        message: str = "Server error occurred.",
        status_code: int = 500,
        response_body: dict[str, Any] | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, request_id)


class MenderConnectionError(MenderError):
    """Exception raised when connection to Mender server fails."""

    def __init__(
        self,
        message: str = "Failed to connect to Mender server.",
        original_error: Exception | None = None,
    ) -> None:
        details = {"original_error": str(original_error)} if original_error else {}
        super().__init__(message, details)
        self.original_error = original_error


class MenderTimeoutError(MenderError):
    """Exception raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out.",
        timeout: float | None = None,
    ) -> None:
        details = {"timeout": timeout} if timeout else {}
        super().__init__(message, details)
        self.timeout = timeout
