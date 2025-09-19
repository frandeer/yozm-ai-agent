from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Tuple

from ai_ops import enrich_with_ai, group_by_category
from config import Config


def load_news(json_path: Path | str) -> Tuple[Dict, List[Dict]]:
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    meta = payload.get("meta", {})
    articles = payload.get("articles", [])
    return meta, articles


def compute_category_stats(grouped: Dict[str, List[Dict]]) -> Tuple[List[Dict], int]:
    total = sum(len(items) for items in grouped.values())
    stats = []
    for category, items in grouped.items():
        if not items:
            continue
        ratio = (len(items) / total * 100) if total else 0
        stats.append({
            "category": category,
            "count": len(items),
            "ratio": ratio,
        })
    stats.sort(key=lambda item: item["count"], reverse=True)
    return stats, total


async def _run_pipeline_async(json_path: Path | str) -> Dict:
    meta, raw_articles = load_news(json_path)
    enriched = await enrich_with_ai(raw_articles)
    grouped = group_by_category(enriched)
    stats, total = compute_category_stats(grouped)
    return {
        "meta": meta,
        "articles": enriched,
        "grouped": grouped,
        "stats": stats,
        "total_count": total,
    }


def run_pipeline(json_path: Path | str) -> Dict:
    Config.validate()
    return asyncio.run(_run_pipeline_async(json_path))
