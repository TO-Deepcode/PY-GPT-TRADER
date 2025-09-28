from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List, Optional, Tuple

import feedparser

from .sources import SOURCES


async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, url)


def ensure_list(value: Any) -> List[Any]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def to_iso(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(value)
        return dt.isoformat()
    except Exception:
        return None


def normalize_entry(source_meta: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
    authors = entry.get("authors") or entry.get("author")
    if isinstance(authors, list):
        authors = [a.get("name") if isinstance(a, dict) else a for a in authors]
    return {
        "source": source_meta["id"],
        "label": source_meta["label"],
        "weight": source_meta.get("weight", 1),
        "focus": source_meta.get("focus", []),
        "title": entry.get("title"),
        "link": entry.get("link"),
        "author": authors,
        "summary": entry.get("summary"),
        "publishedAt": to_iso(entry.get("published")),
        "raw": entry,
    }


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: item.get("publishedAt") or "",
        reverse=True,
    )


async def fetch_source_news(source_id: str, *, limit: int = 25) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[str]]:
    source_meta = SOURCES.get(source_id)
    if not source_meta:
        return source_id, None, "Unsupported source"
    try:
        parsed = await fetch_feed(source_meta["feed"])
    except Exception as exc:  # noqa: BLE001
        return source_id, None, str(exc)
    entries = ensure_list(parsed.get("entries"))[:limit]
    items = [normalize_entry(source_meta, entry) for entry in entries]
    return source_id, items, None


async def fetch_news_aggregate(
    sources: Optional[Iterable[str]] = None,
    *,
    limit_per_source: int = 20,
    max_items: int = 100,
) -> Dict[str, Any]:
    source_list = list(sources) if sources else list(SOURCES.keys())

    results = await asyncio.gather(
        *(fetch_source_news(source_id, limit=limit_per_source) for source_id in source_list)
    )

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for source_id, source_items, error in results:
        if error:
            errors.append({"source": source_id, "message": error})
            continue
        if source_items:
            items.extend(source_items)

    items = sort_items(items)[:max_items]

    return {
        "status": "partial" if errors else "ok",
        "requestedSources": source_list,
        "availableSources": SOURCES,
        "total": len(items),
        "items": items,
        "errors": errors,
    }
