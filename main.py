import asyncio
import os
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from clients.bybit import fetch_bybit_klines, fetch_bybit_orderbook, fetch_bybit_recent_trades
from clients.binance import (
    fetch_binance_futures_klines,
    fetch_binance_futures_orderbook,
    fetch_binance_futures_trades,
    fetch_binance_spot_klines,
    fetch_binance_spot_orderbook,
    fetch_binance_spot_trades,
)
from clients.coinmarketcap import fetch_cmc_global_metrics, fetch_cmc_quotes
from news.aggregator import fetch_news_aggregate

BYBIT_INTERVAL_MAP = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "12h": "720",
    "1d": "D",
    "1D": "D",
    "1day": "D",
}


def normalize_bybit_interval(interval: Optional[str]) -> str:
    if not interval:
        return "60"
    key = interval.strip()
    lower = key.lower()
    if key in BYBIT_INTERVAL_MAP:
        return BYBIT_INTERVAL_MAP[key]
    if lower in BYBIT_INTERVAL_MAP:
        return BYBIT_INTERVAL_MAP[lower]
    if key.isdigit():
        return key
    return "60"


async def settle(callable_awaitable):
    try:
        data = await callable_awaitable
        return {"data": data}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


app = FastAPI(title="Atlas T7 Python Market Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ATLAS_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/bybit")
async def get_bybit_metric(
    symbol: str,
    metric: str = "klines",
    interval: str = "60",
    limit: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
):
    metric = metric.lower()
    if metric == "klines":
        data = await fetch_bybit_klines(symbol=symbol, interval=interval, limit=limit, start=start, end=end)
    elif metric == "orderbook":
        data = await fetch_bybit_orderbook(symbol=symbol, limit=limit)
    elif metric == "trades":
        data = await fetch_bybit_recent_trades(symbol=symbol, limit=limit)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")
    return {"source": "bybit", "metric": metric, "symbol": symbol, "data": data}


@app.get("/api/binance")
async def get_binance_metric(
    symbol: str,
    market: str = "futures",
    metric: str = "klines",
    interval: str = "1h",
    limit: Optional[int] = None,
    startTime: Optional[int] = None,
    endTime: Optional[int] = None,
):
    market = market.lower()
    metric = metric.lower()

    if market == "spot":
        if metric == "klines":
            data = await fetch_binance_spot_klines(symbol=symbol, interval=interval, limit=limit, startTime=startTime, endTime=endTime)
        elif metric == "orderbook":
            data = await fetch_binance_spot_orderbook(symbol=symbol, limit=limit)
        elif metric == "trades":
            data = await fetch_binance_spot_trades(symbol=symbol, limit=limit)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")
    else:
        if metric == "klines":
            data = await fetch_binance_futures_klines(symbol=symbol, interval=interval, limit=limit, startTime=startTime, endTime=endTime)
        elif metric == "orderbook":
            data = await fetch_binance_futures_orderbook(symbol=symbol, limit=limit)
        elif metric == "trades":
            data = await fetch_binance_futures_trades(symbol=symbol, limit=limit)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")

    return {"source": "binance", "market": market, "metric": metric, "symbol": symbol, "data": data}


@app.get("/api/cmc")
async def get_cmc_data(metric: str = "quotes", symbols: Optional[str] = None, convert: str = "USD"):
    metric = metric.lower()
    if metric == "quotes":
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols query param is required for quotes metric")
        symbol_list = [token.strip() for token in symbols.split(",") if token.strip()]
        data = await fetch_cmc_quotes(symbols=symbol_list, convert=convert)
        return {"source": "coinmarketcap", "metric": metric, "convert": convert, "data": data}
    if metric == "global-metrics":
        data = await fetch_cmc_global_metrics(convert=convert)
        return {"source": "coinmarketcap", "metric": metric, "convert": convert, "data": data}
    raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")


@app.get("/api/news")
async def get_crypto_news(
    source: Optional[str] = None,
    mode: str = "aggregate",
    limitPerSource: int = 20,
    maxItems: int = 100,
):
    sources: Optional[List[str]] = None
    if source:
        sources = [token.strip() for token in source.split(",") if token.strip()]

    if mode == "single":
        if not sources or len(sources) != 1:
            raise HTTPException(status_code=400, detail="mode=single requires exactly one source")
        response = await fetch_news_aggregate(sources, limit_per_source=limitPerSource, max_items=limitPerSource)
        response["status"] = "ok" if not response["errors"] else "partial"
        return response

    return await fetch_news_aggregate(sources, limit_per_source=limitPerSource, max_items=maxItems)


@app.get("/api/market")
async def get_unified_market_snapshot(
    symbol: str,
    interval: str = "1h",
    limit: int = 200,
    convert: str = "USD",
):
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol query param is required")

    bybit_interval = normalize_bybit_interval(interval)

    results = await asyncio.gather(
        settle(fetch_bybit_klines(symbol=symbol, interval=bybit_interval, limit=limit)),
        settle(fetch_bybit_orderbook(symbol=symbol, limit=50)),
        settle(fetch_bybit_recent_trades(symbol=symbol, limit=min(limit, 200))),
        settle(fetch_binance_futures_klines(symbol=symbol, interval=interval, limit=limit)),
        settle(fetch_binance_futures_orderbook(symbol=symbol, limit=100)),
        settle(fetch_binance_futures_trades(symbol=symbol, limit=min(limit, 1000))),
        settle(fetch_cmc_quotes(symbols=[symbol.replace("USDT", "")], convert=convert)),
    )

    labels = [
        "bybit.klines",
        "bybit.orderbook",
        "bybit.trades",
        "binance.klines",
        "binance.orderbook",
        "binance.trades",
        "coinmarketcap.quotes",
    ]

    errors = []
    payload = {
        "symbol": symbol,
        "interval": interval,
        "convert": convert,
        "bybit": {
            "klines": results[0].get("data"),
            "orderbook": results[1].get("data"),
            "trades": results[2].get("data"),
        },
        "binance": {
            "klines": results[3].get("data"),
            "orderbook": results[4].get("data"),
            "trades": results[5].get("data"),
        },
        "coinmarketcap": results[6].get("data"),
    }

    for label, result in zip(labels, results):
        if result.get("error"):
            errors.append({"source": label, "message": result["error"]})

    status_code = 207 if errors else 200
    response_status = "partial" if errors else "ok"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": response_status,
            "errors": errors,
            "data": payload,
        },
    )
