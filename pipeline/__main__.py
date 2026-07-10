"""Run the daily digest pipeline: fetch, vet, dedupe, publish JSON."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import aggregate, fetch_arxiv, fetch_github, fetch_news

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("--config", default=str(REPO_ROOT / "pipeline" / "config.yaml"))
    parser.add_argument("--data-dir", default=str(REPO_ROOT / "site" / "data"))
    parser.add_argument("--seen-path", default=str(REPO_ROOT / "state" / "seen.json"))
    args = parser.parse_args(argv)

    config = yaml.safe_load(Path(args.config).read_text())
    now = datetime.now(timezone.utc)
    date_str = now.date().isoformat()

    announcements, news_errors = fetch_news.fetch_news(
        config["news_sources"], config["ai_keywords"], now, config["news_lookback_days"]
    )
    repos, github_errors = fetch_github.fetch_github(config["github"], now)
    papers, arxiv_errors = fetch_arxiv.fetch_arxiv(
        config["arxiv"], config["research_keywords"], now
    )
    errors = news_errors + github_errors + arxiv_errors
    raw_total = len(announcements) + len(repos) + len(papers)

    if raw_total == 0 and errors:
        print("All sources failed; not publishing an empty digest.", file=sys.stderr)
        for error in errors:
            print(f"  {error['source']}: {error['message']}", file=sys.stderr)
        return 1

    seen = aggregate.load_seen(args.seen_path)
    announcements = aggregate.filter_new(announcements, seen, date_str)
    repos = aggregate.filter_new(repos, seen, date_str)
    papers = aggregate.filter_new(papers, seen, date_str)

    for group in (announcements, repos, papers):
        aggregate.mark_seen(group, seen, date_str)

    digest = aggregate.build_digest(
        date_str, now.isoformat(timespec="seconds"), announcements, repos, papers, errors
    )
    day_path = aggregate.write_digest(digest, args.data_dir)
    aggregate.save_seen(seen, args.seen_path)
    print(
        f"Wrote {day_path}: {len(announcements)} announcements, "
        f"{len(repos)} repos, {len(papers)} papers, {len(errors)} source errors"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
