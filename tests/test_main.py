import json

from pipeline import __main__ as main_mod
from pipeline import fetch_arxiv, fetch_github, fetch_news

ANNOUNCEMENT = {
    "id": "https://example.com/a",
    "title": "A thing",
    "url": "https://example.com/a",
    "source": "openai",
    "published": None,
    "snippet": "",
    "score": 1.0,
    "signals": [],
}
REPO = {
    "id": "acme/kit",
    "title": "acme/kit",
    "url": "https://github.com/acme/kit",
    "description": "",
    "stars": 100,
    "language": "Python",
    "topics": [],
    "created_at": "2026-07-01T00:00:00Z",
    "score": 6.66,
    "signals": ["new"],
}


def run(tmp_path):
    return main_mod.main(
        ["--data-dir", str(tmp_path / "data"), "--seen-path", str(tmp_path / "seen.json")]
    )


def test_main_writes_digest_and_seen_state(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_news, "fetch_news", lambda *a, **k: ([ANNOUNCEMENT], []))
    monkeypatch.setattr(fetch_github, "fetch_github", lambda *a, **k: ([REPO], []))
    monkeypatch.setattr(
        fetch_arxiv, "fetch_arxiv", lambda *a, **k: ([], [{"source": "arxiv", "message": "boom"}])
    )

    assert run(tmp_path) == 0

    day_files = [p for p in (tmp_path / "data").glob("*-*-*.json")]
    assert len(day_files) == 1
    digest = json.loads(day_files[0].read_text())
    assert digest["categories"]["announcements"][0]["id"] == ANNOUNCEMENT["id"]
    assert digest["categories"]["github"][0]["id"] == "acme/kit"
    assert digest["errors"] == [{"source": "arxiv", "message": "boom"}]

    seen = json.loads((tmp_path / "seen.json").read_text())
    assert set(seen) == {ANNOUNCEMENT["id"], "acme/kit"}

    index = json.loads((tmp_path / "data" / "index.json").read_text())
    assert index == [digest["date"]]


def test_main_dedupes_on_second_run(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_news, "fetch_news", lambda *a, **k: ([ANNOUNCEMENT], []))
    monkeypatch.setattr(fetch_github, "fetch_github", lambda *a, **k: ([], []))
    monkeypatch.setattr(fetch_arxiv, "fetch_arxiv", lambda *a, **k: ([], []))

    assert run(tmp_path) == 0
    assert run(tmp_path) == 0  # same-day rerun: same item again, still succeeds

    day_files = [p for p in (tmp_path / "data").glob("*-*-*.json")]
    digest = json.loads(day_files[0].read_text())
    # same-day reruns must be idempotent: the announcement is still there
    assert digest["categories"]["announcements"][0]["id"] == ANNOUNCEMENT["id"]


def test_main_dedupes_items_seen_on_an_earlier_day(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_news, "fetch_news", lambda *a, **k: ([ANNOUNCEMENT], []))
    monkeypatch.setattr(fetch_github, "fetch_github", lambda *a, **k: ([], []))
    monkeypatch.setattr(fetch_arxiv, "fetch_arxiv", lambda *a, **k: ([], []))

    seen_path = tmp_path / "seen.json"
    seen_path.write_text(json.dumps({ANNOUNCEMENT["id"]: "2026-07-09"}))

    assert run(tmp_path) == 0

    day_files = [p for p in (tmp_path / "data").glob("*-*-*.json")]
    digest = json.loads(day_files[0].read_text())
    # an item already seen on an earlier day is deduped, not republished
    assert digest["categories"]["announcements"] == []


def test_main_fails_when_all_sources_error(tmp_path, monkeypatch):
    error = [{"source": "x", "message": "down"}]
    monkeypatch.setattr(fetch_news, "fetch_news", lambda *a, **k: ([], error))
    monkeypatch.setattr(fetch_github, "fetch_github", lambda *a, **k: ([], error))
    monkeypatch.setattr(fetch_arxiv, "fetch_arxiv", lambda *a, **k: ([], error))

    assert run(tmp_path) == 1
    assert not (tmp_path / "data").exists()  # nothing published


def test_main_succeeds_when_fully_deduped_even_with_a_source_error(tmp_path, monkeypatch):
    # A quiet day where every fetched item was already published on an earlier
    # day (fully deduped) plus one unrelated source error must NOT be treated
    # as "all sources failed" -- raw items were fetched, so we still publish.
    monkeypatch.setattr(fetch_news, "fetch_news", lambda *a, **k: ([ANNOUNCEMENT], []))
    monkeypatch.setattr(fetch_github, "fetch_github", lambda *a, **k: ([], []))
    error = [{"source": "arxiv", "message": "boom"}]
    monkeypatch.setattr(fetch_arxiv, "fetch_arxiv", lambda *a, **k: ([], error))

    seen_path = tmp_path / "seen.json"
    seen_path.write_text(json.dumps({ANNOUNCEMENT["id"]: "2026-07-09"}))

    assert run(tmp_path) == 0

    day_files = [p for p in (tmp_path / "data").glob("*-*-*.json")]
    assert len(day_files) == 1
    digest = json.loads(day_files[0].read_text())
    assert digest["categories"]["announcements"] == []
    assert digest["errors"] == error
