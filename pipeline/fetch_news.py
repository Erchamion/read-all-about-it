"""Fetch company announcements from RSS/Atom feeds and scraped news pages."""

import calendar
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import feedparser
from bs4 import BeautifulSoup

from .http import get_with_retry
from .vetting import keyword_matches

USER_AGENT = "read-all-about-it/1.0 (+https://github.com/jonstaten/read-all-about-it)"
MIN_TITLE_LENGTH = 8


def default_fetcher(url):
    response = get_with_retry(url, headers={"User-Agent": USER_AGENT})
    return response.text


def entry_published(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)


def _strip_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)


def parse_rss(source, content, keywords, now, lookback_days):
    cutoff = now - timedelta(days=lookback_days)
    items = []
    for entry in feedparser.parse(content).entries:
        published = entry_published(entry)
        if published is not None and published < cutoff:
            continue
        title = entry.get("title", "").strip()
        url = entry.get("link", "")
        snippet = _strip_html(entry.get("summary", ""))[:300]
        signals = []
        if source.get("filter"):
            matches = keyword_matches(f"{title} {snippet}", keywords)
            if not matches:
                continue
            signals = [f"keyword:{m}" for m in matches]
        items.append(
            {
                "id": url,
                "title": title,
                "url": url,
                "source": source["name"],
                "published": published.isoformat() if published else None,
                "snippet": snippet,
                "score": 1.0 + len(signals),
                "signals": signals,
            }
        )
    return items


def parse_scrape(source, html):
    """Extract article links from a news index page. Scraped items have no
    publish date; seen.json dedupe makes first-sighting the publish day."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_urls = set()
    for link in soup.select(source["item_selector"]):
        href = link.get("href")
        title = link.get_text(" ", strip=True)
        if not href or len(title) < MIN_TITLE_LENGTH:
            continue
        url = urljoin(source["base_url"], href)
        if url in seen_urls or url.rstrip("/") == source["url"].rstrip("/"):
            continue
        seen_urls.add(url)
        items.append(
            {
                "id": url,
                "title": title,
                "url": url,
                "source": source["name"],
                "published": None,
                "snippet": "",
                "score": 1.0,
                "signals": ["scraped"],
            }
        )
    return items


def fetch_news(sources, keywords, now, lookback_days, fetcher=default_fetcher):
    items, errors = [], []
    for source in sources:
        try:
            content = fetcher(source["url"])
            if source["type"] == "rss":
                items.extend(parse_rss(source, content, keywords, now, lookback_days))
            else:
                items.extend(parse_scrape(source, content))
        except Exception as error:
            errors.append({"source": source["name"], "message": str(error)})
    return items, errors
