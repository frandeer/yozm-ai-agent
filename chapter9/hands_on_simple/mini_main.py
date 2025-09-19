from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from pipeline import run_pipeline
from renderers import render_json_report, render_markdown_report

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT = BASE_DIR / "data" / "news_sample.json"
OUTPUT_DIR = BASE_DIR / "outputs"

FORMATS = {
    "markdown": ("md", render_markdown_report),
    "json": ("json", render_json_report),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenAI를 호출하여 요약과 분류를 수행하는 미니 뉴스 파이프라인"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="뉴스 기사 JSON 입력 경로",
    )
    parser.add_argument(
        "--format",
        choices=FORMATS.keys(),
        default="markdown",
        help="출력 포맷 (markdown 또는 json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="출력 파일 경로를 직접 지정",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_data = run_pipeline(args.input)

    extension, renderer = FORMATS[args.format]
    content = renderer(report_data)

    output_path = args.output
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"mini_report_{timestamp}.{extension}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    print(f"Saved {args.format} report to {output_path}")
    print(f"Articles processed: {report_data['total_count']}")
    if report_data["stats"]:
        print("Category summary:")
        for stat in report_data["stats"]:
            print(f"  - {stat['category']}: {stat['count']}건 ({stat['ratio']:.1f}%)")
    else:
        print("Category summary: no articles available")


if __name__ == "__main__":
    main()
