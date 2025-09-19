from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List

from config import Config

_MARKDOWN_HEADER = "# Mini Google News Report"
_NOTE = "*본 샘플 데이터는 정치 기사를 제외한 항목으로 구성되었습니다.*"


def _ordered_categories(grouped: Dict[str, List[Dict]]) -> List[str]:
    base_order = [cat for cat in Config.CATEGORIES if grouped.get(cat)]
    extras = sorted(
        cat for cat in grouped.keys() if cat not in Config.CATEGORIES and grouped.get(cat)
    )
    return base_order + extras


def render_markdown_report(report_data: Dict) -> str:
    meta = report_data.get("meta", {})
    grouped = report_data.get("grouped", {})
    stats = report_data.get("stats", [])
    total = report_data.get("total_count", 0)

    collected_at = meta.get("collected_at", "-")
    source = meta.get("source", "-")

    lines: List[str] = [_MARKDOWN_HEADER, "", "## 기본 정보"]
    lines.append(f"- 수집 시각: {collected_at}")
    lines.append(f"- 데이터 소스: {source}")
    lines.append(f"- 기사 수: {total}건")
    lines.append("")
    lines.append(_NOTE)

    if stats:
        lines.extend(["", "## 카테고리별 뉴스 분포", "", "| 카테고리 | 뉴스 수 | 비율 |", "|---------|--------|------|"])
        for item in stats:
            lines.append(f"| {item['category']} | {item['count']}건 | {item['ratio']:.1f}% |")

    for category in _ordered_categories(grouped):
        articles = grouped.get(category, [])
        if not articles:
            continue
        lines.extend(["", f"## {category} ({len(articles)}건)"])
        for index, article in enumerate(articles, start=1):
            lines.extend(
                [
                    "",
                    f"### {index}. {article.get('title', '제목 없음')}",
                    f"- 출처: {article.get('source', '-')}",
                    f"- 발행: {article.get('published_at', '-')}",
                    f"- 요약: {article.get('summary') or article.get('content', '-')}",
                    f"- 링크: {article.get('url', '-')}",
                ]
            )

    return "\n".join(lines)


def render_json_report(report_data: Dict) -> str:
    grouped = report_data.get("grouped", {})
    stats = report_data.get("stats", [])

    categories_payload = []
    for category in _ordered_categories(grouped):
        articles = grouped.get(category, [])
        if not articles:
            continue
        categories_payload.append(
            {
                "name": category,
                "count": len(articles),
                "articles": articles,
            }
        )

    payload = {
        "meta": report_data.get("meta", {}),
        "stats": stats,
        "categories": categories_payload,
        "notes": ["정치 카테고리는 데이터에서 제외되었습니다."],
        "generated_at": datetime.utcnow().isoformat(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
