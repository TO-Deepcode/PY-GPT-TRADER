import os
from typing import Any, Dict, Optional

import httpx

DEFAULT_TIMEOUT = float(os.getenv("ATLAS_HTTP_TIMEOUT", "8"))

DEFAULT_HEADERS = {
    "User-Agent": os.getenv("ATLAS_USER_AGENT", "Atlas-T7-Python/1.0"),
    "Accept": "application/json,text/plain,*/*",
}


class HttpError(Exception):
    """Custom HTTP error for upstream failures."""

    def __init__(self, message: str, status: int, payload: Optional[Any] = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


async def safe_fetch(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> Any:
    request_headers = {**DEFAULT_HEADERS, **(headers or {})}
    request_timeout = timeout or DEFAULT_TIMEOUT

    async with httpx.AsyncClient(timeout=request_timeout) as client:
        response = await client.get(url, headers=request_headers)
    if response.status_code >= 400:
        raise HttpError(
            f"Request failed with status {response.status_code}",
            response.status_code,
            response.text,
        )

    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    return response.text
