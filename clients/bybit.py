import os
from typing import Any, Dict, Optional

from .http import safe_fetch

BYBIT_BASE_URL = os.getenv("BYBIT_BASE_URL", "https://api.bybit.com")
BYBIT_HEADERS = {
    "Origin": os.getenv("BYBIT_ORIGIN", "https://www.bybit.com"),
    "Referer": os.getenv("BYBIT_REFERER", "https://www.bybit.com"),
}


def _build_url(path: str, params: Dict[str, Any]) -> str:
    from urllib.parse import urlencode

    query = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{BYBIT_BASE_URL}{path}?{query}"


async def fetch_bybit_klines(
    *,
    symbol: str,
    interval: str = "60",
    limit: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> Any:
    url = _build_url(
        "/v5/market/kline",
        {
            "category": os.getenv("BYBIT_CATEGORY", "linear"),
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "start": start,
            "end": end,
        },
    )
    response = await safe_fetch(url, headers=BYBIT_HEADERS)
    return response.get("result", {}).get("list", [])


async def fetch_bybit_orderbook(*, symbol: str, limit: Optional[int] = None) -> Any:
    url = _build_url(
        "/v5/market/orderbook",
        {
            "category": os.getenv("BYBIT_CATEGORY", "linear"),
            "symbol": symbol,
            "limit": limit or 50,
        },
    )
    response = await safe_fetch(url, headers=BYBIT_HEADERS)
    return response.get("result", {})


async def fetch_bybit_recent_trades(*, symbol: str, limit: Optional[int] = None) -> Any:
    url = _build_url(
        "/v5/market/recent-trade",
        {
            "category": os.getenv("BYBIT_CATEGORY", "linear"),
            "symbol": symbol,
            "limit": limit or 200,
        },
    )
    response = await safe_fetch(url, headers=BYBIT_HEADERS)
    return response.get("result", {}).get("list", [])
