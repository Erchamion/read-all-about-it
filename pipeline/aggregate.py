"""Dedupe against history, rank, and persist daily digest JSON."""

import json
from pathlib import Path


def load_seen(path):
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def filter_new(items, seen):
    return [item for item in items if item["id"] not in seen]


def mark_seen(items, seen, date_str):
    for item in items:
        seen[item["id"]] = date_str


def save_seen(seen, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, indent=0, sort_keys=True) + "\n")


def _ranked(items):
    return sorted(items, key=lambda item: item["score"], reverse=True)


def build_digest(date_str, generated_at, announcements, github, research, errors):
    return {
        "date": date_str,
        "generated_at": generated_at,
        "errors": errors,
        "categories": {
            "announcements": _ranked(announcements),
            "github": _ranked(github),
            "research": _ranked(research),
        },
    }


def write_digest(digest, data_dir):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    day_path = data_dir / f"{digest['date']}.json"
    day_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n")
    dates = sorted((p.stem for p in data_dir.glob("*-*-*.json")), reverse=True)
    (data_dir / "index.json").write_text(json.dumps(dates, indent=2) + "\n")
    return day_path
