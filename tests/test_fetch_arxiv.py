from datetime import datetime, timezone

from pipeline.fetch_arxiv import fetch_arxiv

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)

CONFIG = {"categories": ["cs.AI", "cs.CL"], "lookback_days": 2, "max_papers": 2, "min_score": 1.0}

ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
<entry>
  <id>http://arxiv.org/abs/2607.01234v1</id>
  <title>Agent  Benchmarks for LLM
  Reasoning</title>
  <summary>We study agent reasoning with a new benchmark.</summary>
  <published>2026-07-10T01:00:00Z</published>
  <author><name>Ada Lovelace</name></author>
  <author><name>Alan Turing</name></author>
  <link href="http://arxiv.org/abs/2607.01234v1" rel="alternate" type="text/html"/>
  <category term="cs.AI"/><category term="cs.CL"/>
</entry>
<entry>
  <id>http://arxiv.org/abs/2607.05678v1</id>
  <title>A survey of sorting networks</title>
  <summary>Sorting things quickly.</summary>
  <published>2026-07-10T02:00:00Z</published>
  <author><name>Bob</name></author>
  <link href="http://arxiv.org/abs/2607.05678v1" rel="alternate" type="text/html"/>
  <category term="cs.DS"/>
</entry>
<entry>
  <id>http://arxiv.org/abs/2606.00001v1</id>
  <title>Old LLM agent paper</title>
  <summary>An agent paper from last month.</summary>
  <published>2026-06-01T00:00:00Z</published>
  <author><name>Carol</name></author>
  <link href="http://arxiv.org/abs/2606.00001v1" rel="alternate" type="text/html"/>
  <category term="cs.AI"/>
</entry>
</feed>"""

KEYWORDS = ["llm", "agent", "reasoning", "benchmark"]


def test_fetch_arxiv_scores_filters_and_normalizes():
    captured = {}

    def fetcher(params):
        captured.update(params)
        return ATOM_FIXTURE

    papers, errors = fetch_arxiv(CONFIG, KEYWORDS, NOW, fetcher=fetcher)
    assert errors == []
    assert captured["search_query"] == "cat:cs.AI OR cat:cs.CL"
    assert captured["sortBy"] == "submittedDate"

    # sorting-networks paper scores 0 (< min_score); June paper outside lookback
    assert [p["id"] for p in papers] == ["2607.01234v1"]
    paper = papers[0]
    assert paper["title"] == "Agent Benchmarks for LLM Reasoning"  # whitespace normalized
    assert paper["url"] == "http://arxiv.org/abs/2607.01234v1"
    assert paper["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert paper["categories"] == ["cs.AI", "cs.CL"]
    assert paper["score"] == 4.0
    assert paper["signals"] == ["keyword:llm", "keyword:agent", "keyword:reasoning", "keyword:benchmark"]


def test_fetch_arxiv_caps_results_at_max_papers():
    config = dict(CONFIG, min_score=0.0)
    papers, _ = fetch_arxiv(config, KEYWORDS, NOW, fetcher=lambda p: ATOM_FIXTURE)
    assert len(papers) == 2  # max_papers=2, sorted by score desc
    assert papers[0]["id"] == "2607.01234v1"


def test_fetch_arxiv_reports_fetch_failure():
    def fetcher(params):
        raise RuntimeError("timeout")

    papers, errors = fetch_arxiv(CONFIG, KEYWORDS, NOW, fetcher=fetcher)
    assert papers == []
    assert errors == [{"source": "arxiv", "message": "timeout"}]


def test_fetch_arxiv_records_error_for_invalid_feed_response():
    # A 200 response that isn't a valid Atom feed (e.g. an HTML error page)
    # must not silently produce an empty, seemingly-quiet digest.
    html_garbage = "<html><body><h1>503 Service Unavailable</h1></body></html>"

    papers, errors = fetch_arxiv(CONFIG, KEYWORDS, NOW, fetcher=lambda params: html_garbage)
    assert papers == []
    assert len(errors) == 1
    assert errors[0]["source"] == "arxiv"
