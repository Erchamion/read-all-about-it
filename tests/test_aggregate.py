import json

from pipeline.aggregate import (
    build_digest,
    filter_new,
    load_seen,
    mark_seen,
    save_seen,
    write_digest,
)


def item(id_, score=1.0):
    return {"id": id_, "score": score}


def test_seen_roundtrip_and_filtering(tmp_path):
    path = tmp_path / "state" / "seen.json"
    seen = load_seen(path)
    assert seen == {}

    items = [item("a"), item("b")]
    assert filter_new(items, seen) == items

    mark_seen(items, seen, "2026-07-10")
    save_seen(seen, path)

    reloaded = load_seen(path)
    assert reloaded == {"a": "2026-07-10", "b": "2026-07-10"}
    assert filter_new([item("a"), item("c")], reloaded) == [item("c")]


def test_build_digest_ranks_each_category_by_score():
    digest = build_digest(
        "2026-07-10",
        "2026-07-10T13:00:00+00:00",
        announcements=[item("low", 1.0), item("high", 5.0)],
        github=[],
        research=[item("paper", 2.0)],
        errors=[{"source": "xai", "message": "HTTP 503"}],
    )
    assert digest["date"] == "2026-07-10"
    assert [i["id"] for i in digest["categories"]["announcements"]] == ["high", "low"]
    assert digest["categories"]["github"] == []
    assert digest["errors"][0]["source"] == "xai"


def test_write_digest_creates_day_file_and_index(tmp_path):
    data_dir = tmp_path / "data"
    for date in ("2026-07-09", "2026-07-10"):
        digest = build_digest(date, f"{date}T13:00:00+00:00", [], [], [], [])
        path = write_digest(digest, data_dir)
        assert path == data_dir / f"{date}.json"

    index = json.loads((data_dir / "index.json").read_text())
    assert index == ["2026-07-10", "2026-07-09"]  # newest first, no index.json entry
    day = json.loads((data_dir / "2026-07-10.json").read_text())
    assert day["categories"] == {"announcements": [], "github": [], "research": []}
