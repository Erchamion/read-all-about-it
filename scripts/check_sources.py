"""Hit every configured news source live and report status + parsed item count.

Usage: .venv/bin/python scripts/check_sources.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import fetch_news  # noqa: E402

LOOKBACK_DAYS = 30  # wide window so a quiet week still proves parsing works


def main():
    root = Path(__file__).resolve().parent.parent
    config = yaml.safe_load((root / "pipeline" / "config.yaml").read_text())
    now = datetime.now(timezone.utc)
    failures = 0
    for source in config["news_sources"]:
        try:
            content = fetch_news.default_fetcher(source["url"])
            if source["type"] == "rss":
                items = fetch_news.parse_rss(
                    source, content, config["ai_keywords"], now, LOOKBACK_DAYS
                )
            else:
                items = fetch_news.parse_scrape(source, content)
            status = "OK  " if items else "WARN"
            if not items:
                failures += 1
            print(f"{status} {source['name']}: {len(items)} items (last {LOOKBACK_DAYS}d)")
        except Exception as error:
            failures += 1
            print(f"FAIL {source['name']}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
