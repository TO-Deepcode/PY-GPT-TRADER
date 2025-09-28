import os
from typing import Any, Dict, Iterable, Optional

from .http import safe_fetch

SPOT_HOSTS: Iterable[str] = (
    host.strip()
    for host in os.getenv(
        "BINANCE_SPOT_HOSTS",
        "https://api.binance.com,https://api1.binance.com,https://data.binance.com",
    ).split(",")
)

FUTURES_HOSTS: Iterable[str] = (
    host.strip()
    for host in os.getenv(
        "BINANCE_FUTURES_HOSTS",
        "https://fapi.binance.com,https://futures.binance.com",
    ).split(",")
)

BINANCE_HEADERS = {
    "Origin": os.getenv("BINANCE_ORIGIN", "https://www.binance.com"),
    "Referer": os.getenv("BINANCE_REFERER", "https://www.binance.com"),
}


def _build_url(base: str, path: str, params: Dict[str, Any]) -> str:
    from urllib.parse import urlencode

    query = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{base}{path}?{query}"


async def _fetch_from_hosts(hosts: Iterable[str], path: str, params: Dict[str, Any]) -> Any:
    last_error: Optional[Exception] = None
    for host in hosts:
        if not host:
            continue
        try:
            url = _build_url(host, path, params)
            return await safe_fetch(url, headers=BINANCE_HEADERS)
        except Exception as exc:  # fallback
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("No Binance hosts available")


async def fetch_binance_futures_klines(
    *, symbol: str, interval: str = "1h", limit: Optional[int] = None, startTime: Optional[int] = None, endTime: Optional[int] = None
) -> Any:
    return await _fetch_from_hosts(
        FUTURES_HOSTS,
        "/fapi/v1/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": startTime,
            "endTime": endTime,
        },
    )


async def fetch_binance_futures_orderbook(*, symbol: str, limit: Optional[int] = None) -> Any:
    return await _fetch_from_hosts(
        FUTURES_HOSTS,
        "/fapi/v1/depth",
        {
            "symbol": symbol,
            "limit": limit or 100,
        },
    )


async def fetch_binance_futures_trades(*, symbol: str, limit: Optional[int] = None) -> Any:
    return await _fetch_from_hosts(
        FUTURES_HOSTS,
        "/fapi/v1/trades",
        {
            "symbol": symbol,
            "limit": limit or 200,
        },
    )


async def fetch_binance_spot_klines(
    *, symbol: str, interval: str = "1h", limit: Optional[int] = None, startTime: Optional[int] = None, endTime: Optional[int] = None
) -> Any:
    return await _fetch_from_hosts(
        SPOT_HOSTS,
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": startTime,
            "endTime": endTime,
        },
    )


async def fetch_binance_spot_orderbook(*, symbol: str, limit: Optional[int] = None) -> Any:
    return await _fetch_from_hosts(
        SPOT_HOSTS,
        "/api/v3/depth",
        {
            "symbol": symbol,
            "limit": limit or 100,
        },
    )


async def fetch_binance_spot_trades(*, symbol: str, limit: Optional[int] = None) -> Any:
    return await _fetch_from_hosts(
        SPOT_HOSTS,
        "/api/v3/trades",
        {
            "symbol": symbol,
            "limit": limit or 200,
        },
    )
