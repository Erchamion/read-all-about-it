from datetime import datetime, timezone

from pipeline.fetch_news import fetch_news, parse_rss, parse_scrape

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)

RSS_FIXTURE = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Blog</title>
<item><title>New AI model released</title>
  <link>https://example.com/ai-model</link>
  <pubDate>Thu, 09 Jul 2026 10:00:00 GMT</pubDate>
  <description>&lt;p&gt;A new model.&lt;/p&gt;</description></item>
<item><title>Quarterly earnings report</title>
  <link>https://example.com/earnings</link>
  <pubDate>Thu, 09 Jul 2026 09:00:00 GMT</pubDate>
  <description>Money stuff</description></item>
<item><title>Old AI post</title>
  <link>https://example.com/old</link>
  <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
  <description>old</description></item>
</channel></rss>"""

HTML_FIXTURE = """<main>
<a href="/news/announcing-thing">Announcing Thing: our new model</a>
<a href="/news">All news</a>
<a href="/news/short">Hi</a>
<a href="/news/announcing-thing">Announcing Thing: our new model</a>
</main>"""


def test_parse_rss_filtered_source_keeps_only_ai_recent_posts():
    source = {"name": "bigco", "type": "rss", "url": "https://x", "filter": True}
    items = parse_rss(source, RSS_FIXTURE, ["ai", "model"], NOW, lookback_days=3)
    assert [i["id"] for i in items] == ["https://example.com/ai-model"]
    item = items[0]
    assert item["source"] == "bigco"
    assert item["snippet"] == "A new model."  # HTML stripped
    assert item["published"] == "2026-07-09T10:00:00+00:00"
    assert item["signals"] == ["keyword:ai", "keyword:model"]
    assert item["score"] == 3.0


def test_parse_rss_unfiltered_source_keeps_all_recent_posts():
    source = {"name": "ailab", "type": "rss", "url": "https://x", "filter": False}
    items = parse_rss(source, RSS_FIXTURE, ["ai", "model"], NOW, lookback_days=3)
    assert [i["id"] for i in items] == [
        "https://example.com/ai-model",
        "https://example.com/earnings",
    ]
    assert items[1]["signals"] == []
    assert items[1]["score"] == 1.0


def test_parse_scrape_extracts_article_links():
    source = {
        "name": "anthropic",
        "type": "scrape",
        "url": "https://www.anthropic.com/news",
        "item_selector": 'a[href^="/news/"]',
        "base_url": "https://www.anthropic.com",
    }
    items = parse_scrape(source, HTML_FIXTURE)
    # index link doesn't match selector, "Hi" too short, duplicate collapsed
    assert [i["url"] for i in items] == ["https://www.anthropic.com/news/announcing-thing"]
    assert items[0]["published"] is None
    assert items[0]["signals"] == ["scraped"]


def test_fetch_news_isolates_source_failures():
    sources = [
        {"name": "good", "type": "rss", "url": "https://good", "filter": False},
        {"name": "bad", "type": "rss", "url": "https://bad", "filter": False},
    ]

    def fetcher(url):
        if url == "https://bad":
            raise RuntimeError("HTTP 503")
        return RSS_FIXTURE

    items, errors = fetch_news(sources, [], NOW, 3, fetcher=fetcher)
    assert len(items) == 2  # two recent posts from the good source
    assert errors == [{"source": "bad", "message": "HTTP 503"}]
