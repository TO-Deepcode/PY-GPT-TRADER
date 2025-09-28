import os
from typing import Any, Dict, Iterable, Optional

from .http import safe_fetch

CMC_BASE_URL = os.getenv("CMC_BASE_URL", "https://pro-api.coinmarketcap.com")
CMC_API_KEY = os.getenv("CMC_API_KEY")

if not CMC_API_KEY:
    # We allow running without the key (e.g. local tests), but emit a warning.
    import warnings

    warnings.warn("CMC_API_KEY is not set; CMC endpoints will fail.")


def _build_url(path: str, params: Dict[str, Any]) -> str:
    from urllib.parse import urlencode

    query = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{CMC_BASE_URL}{path}?{query}"


async def fetch_cmc_quotes(*, symbols: Iterable[str], convert: str = "USD") -> Any:
    if not CMC_API_KEY:
        raise RuntimeError("CMC_API_KEY missing")
    symbol_param = ",".join(symbols)
    url = _build_url(
        "/v1/cryptocurrency/quotes/latest",
        {
            "symbol": symbol_param,
            "convert": convert,
        },
    )
    return await safe_fetch(url, headers={"X-CMC_PRO_API_KEY": CMC_API_KEY})


async def fetch_cmc_global_metrics(*, convert: str = "USD") -> Any:
    if not CMC_API_KEY:
        raise RuntimeError("CMC_API_KEY missing")
    url = _build_url(
        "/v1/global-metrics/quotes/latest",
        {
            "convert": convert,
        },
    )
    return await safe_fetch(url, headers={"X-CMC_PRO_API_KEY": CMC_API_KEY})
