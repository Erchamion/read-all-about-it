"""Fetch and rank recent papers from the arxiv API (Atom)."""

from datetime import timedelta

import feedparser

from .fetch_news import USER_AGENT, entry_published
from .http import get_with_retry
from .vetting import keyword_matches, score_paper

API_URL = "https://export.arxiv.org/api/query"
FETCH_WINDOW = 200  # newest submissions to scan per run


def default_fetcher(params):
    response = get_with_retry(
        API_URL, params=params, timeout=60, headers={"User-Agent": USER_AGENT}
    )
    return response.text


def _normalize(text):
    return " ".join((text or "").split())


def fetch_arxiv(config, keywords, now, fetcher=default_fetcher):
    params = {
        "search_query": " OR ".join(f"cat:{c}" for c in config["categories"]),
        "start": 0,
        "max_results": FETCH_WINDOW,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        content = fetcher(params)
    except Exception as error:
        return [], [{"source": "arxiv", "message": str(error)}]

    parsed = feedparser.parse(content)
    if parsed.bozo or not parsed.entries:
        message = (
            f"arxiv response was not a valid Atom feed "
            f"(bozo={bool(parsed.bozo)}, entries={len(parsed.entries)})"
        )
        return [], [{"source": "arxiv", "message": message}]

    cutoff = now - timedelta(days=config["lookback_days"])
    papers = []
    for entry in parsed.entries:
        published = entry_published(entry)
        if published is None or published < cutoff:
            continue
        title = _normalize(entry.get("title"))
        abstract = _normalize(entry.get("summary"))
        matches = keyword_matches(f"{title} {abstract}", keywords)
        score = score_paper(matches)
        if score < config["min_score"]:
            continue
        papers.append(
            {
                "id": entry.get("id", "").rsplit("/", 1)[-1],
                "title": title,
                "url": entry.get("link", ""),
                "authors": [a.get("name") for a in entry.get("authors", [])][:6],
                "snippet": abstract[:400],
                "categories": [t.get("term") for t in entry.get("tags", [])],
                "published": published.isoformat(),
                "score": score,
                "signals": [f"keyword:{m}" for m in matches],
            }
        )
    papers.sort(key=lambda p: p["score"], reverse=True)
    return papers[: config["max_papers"]], []
