"""
HTTP client utilities for Mender SDK.
"""

from __future__ import annotations

import logging
from typing import Any, BinaryIO

import httpx

from mender_sdk.exceptions import (
    MenderAPIError,
    MenderAuthenticationError,
    MenderAuthorizationError,
    MenderConflictError,
    MenderConnectionError,
    MenderNotFoundError,
    MenderRateLimitError,
    MenderServerError,
    MenderTimeoutError,
    MenderValidationError,
)
from mender_sdk.utils.retry import RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP client for making requests to Mender API.

    Handles authentication, error responses, retries, and request/response logging.
    """

    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BASE_URL = "https://hosted.mender.io"

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: RetryConfig | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for the Mender API.
            token: JWT authentication token.
            timeout: Request timeout in seconds.
            retry_config: Configuration for retry behavior.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.verify_ssl = verify_ssl
        self._client: httpx.AsyncClient | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> HTTPClient:
        """Enter async context manager."""
        await self._get_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    def _handle_error_response(
        self,
        response: httpx.Response,
        request_id: str | None = None,
    ) -> None:
        """
        Handle error responses from the API.

        Args:
            response: HTTP response object.
            request_id: Request ID for tracking.

        Raises:
            Appropriate MenderAPIError subclass based on status code.
        """
        status_code = response.status_code

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        error_message = self._extract_error_message(response_body)

        error_classes: dict[int, type[MenderAPIError]] = {
            400: MenderValidationError,
            401: MenderAuthenticationError,
            403: MenderAuthorizationError,
            404: MenderNotFoundError,
            409: MenderConflictError,
            429: MenderRateLimitError,
        }

        if status_code in error_classes:
            error_class = error_classes[status_code]
            if status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise MenderRateLimitError(
                    message=error_message,
                    response_body=response_body,
                    request_id=request_id,
                    retry_after=int(retry_after) if retry_after else None,
                )
            raise error_class(
                message=error_message,
                response_body=response_body,
                request_id=request_id,
            )

        if 500 <= status_code < 600:
            raise MenderServerError(
                message=error_message,
                status_code=status_code,
                response_body=response_body,
                request_id=request_id,
            )

        raise MenderAPIError(
            message=error_message,
            status_code=status_code,
            response_body=response_body,
            request_id=request_id,
        )

    def _extract_error_message(
        self,
        response_body: dict[str, Any] | str | None,
    ) -> str:
        """Extract error message from response body."""
        if isinstance(response_body, dict):
            return (
                response_body.get("error")
                or response_body.get("message")
                or response_body.get("Error")
                or str(response_body)
            )
        return str(response_body) if response_body else "Unknown error"

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, BinaryIO, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Make an HTTP request.

        Args:
            method: HTTP method.
            path: API endpoint path.
            params: Query parameters.
            json_data: JSON request body.
            data: Form data.
            files: Files to upload.
            headers: Additional headers.

        Returns:
            HTTP response object.

        Raises:
            MenderConnectionError: If connection fails.
            MenderTimeoutError: If request times out.
            MenderAPIError: If API returns an error.
        """
        client = await self._get_client()
        request_headers = {**self._headers, **(headers or {})}

        # Remove Content-Type for file uploads (let httpx set it)
        if files:
            request_headers.pop("Content-Type", None)

        request_id = None

        logger.debug(
            "Making %s request to %s with params=%s",
            method,
            path,
            params,
        )

        try:
            response = await client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
                data=data,
                files=files,
                headers=request_headers,
            )

            request_id = response.headers.get("X-Request-Id")

            logger.debug(
                "Received response: status=%d, request_id=%s",
                response.status_code,
                request_id,
            )

            if not response.is_success:
                self._handle_error_response(response, request_id)

            return response

        except httpx.ConnectError as e:
            raise MenderConnectionError(
                message=f"Failed to connect to {self.base_url}",
                original_error=e,
            ) from e
        except httpx.TimeoutException as e:
            raise MenderTimeoutError(
                message=f"Request to {path} timed out",
                timeout=self.timeout,
            ) from e

    @retry_with_backoff()
    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a GET request."""
        return await self._request("GET", path, params=params, headers=headers)

    @retry_with_backoff()
    async def post(
        self,
        path: str,
        json_data: dict[str, Any] | list[Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, BinaryIO, str]] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a POST request."""
        return await self._request(
            "POST",
            path,
            json_data=json_data,
            data=data,
            files=files,
            params=params,
            headers=headers,
        )

    @retry_with_backoff()
    async def put(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a PUT request."""
        return await self._request(
            "PUT", path, json_data=json_data, params=params, headers=headers
        )

    @retry_with_backoff()
    async def patch(
        self,
        path: str,
        json_data: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a PATCH request."""
        return await self._request(
            "PATCH", path, json_data=json_data, params=params, headers=headers
        )

    @retry_with_backoff()
    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make a DELETE request."""
        return await self._request("DELETE", path, params=params, headers=headers)

    async def get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a GET request and return JSON response."""
        response = await self.get(path, params=params)
        return response.json()

    async def post_json(
        self,
        path: str,
        json_data: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a POST request and return JSON response."""
        response = await self.post(path, json_data=json_data, params=params)
        if response.content:
            return response.json()
        return None

    async def download(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """Download binary content."""
        response = await self.get(path, params=params)
        return response.content
