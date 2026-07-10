from datetime import datetime, timezone

from pipeline.fetch_github import fetch_github

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)

CONFIG = {
    "new": {"created_within_days": 7, "min_stars": 15},
    "rising": {"created_within_days": 60, "min_stars": 200},
    "search_terms": ["ai agent", "mcp server"],
    "per_query_limit": 30,
    "repo_keywords": ["agent", "llm", "mcp"],
}

REPO = {
    "full_name": "acme/agent-kit",
    "html_url": "https://github.com/acme/agent-kit",
    "description": "An LLM agent toolkit",
    "stargazers_count": 255,
    "language": "Python",
    "topics": ["llm", "agents", "mcp"],
    "created_at": "2026-07-05T00:00:00Z",
}


def test_fetch_github_builds_queries_and_transforms_items():
    queries = []

    def fetcher(params):
        queries.append(params["q"])
        return {"items": [REPO]} if len(queries) == 1 else {"items": []}

    items, errors = fetch_github(CONFIG, NOW, fetcher=fetcher)
    assert errors == []
    # 2 modes x 2 terms = 4 queries with correct date/star cutoffs
    assert queries[0] == '"ai agent" created:>=2026-07-03 stars:>=15'
    assert queries[2] == '"ai agent" created:>=2026-05-11 stars:>=200'
    assert len(queries) == 4

    assert len(items) == 1
    item = items[0]
    assert item["id"] == "acme/agent-kit"
    assert item["stars"] == 255
    # matches: agent (name+desc), llm (desc), mcp (topics) -> log2(256) + 3
    assert item["score"] == 11.0
    assert item["signals"] == ["new", "keyword:agent", "keyword:llm", "keyword:mcp"]


def test_fetch_github_dedupes_across_queries():
    items, errors = fetch_github(CONFIG, NOW, fetcher=lambda params: {"items": [REPO]})
    assert len(items) == 1  # returned by all 4 queries, kept once
    assert items[0]["signals"][0] == "new"  # first mode wins


def test_fetch_github_records_query_failures_and_continues():
    def fetcher(params):
        if "mcp server" in params["q"]:
            raise RuntimeError("rate limited")
        return {"items": [REPO]}

    items, errors = fetch_github(CONFIG, NOW, fetcher=fetcher)
    assert len(items) == 1
    assert len(errors) == 2  # one per mode for the failing term
    assert errors[0]["source"] == "github:new:mcp server"


def test_fetch_github_records_malformed_items_and_continues():
    call_count = [0]

    def fetcher(params):
        call_count[0] += 1
        # First call has malformed item (missing full_name), valid item
        if call_count[0] == 1:
            return {
                "items": [
                    {"bad": "data"},  # missing full_name
                    REPO,  # valid
                ]
            }
        # Other calls return just valid items
        return {"items": [REPO] if call_count[0] == 2 else []}

    items, errors = fetch_github(CONFIG, NOW, fetcher=fetcher)
    # Should return the valid item from first query, no items from others (dedupe)
    assert len(items) == 1
    assert items[0]["id"] == "acme/agent-kit"
    # Should record error for malformed item in first query
    assert len(errors) == 1
    assert errors[0]["source"] == "github:new:ai agent"
    assert "full_name" in errors[0]["message"]
