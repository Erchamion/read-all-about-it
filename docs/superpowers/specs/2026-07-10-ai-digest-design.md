# Read All About It — Daily AI Intelligence Digest

**Date:** 2026-07-10
**Status:** Approved

## Purpose

A daily-updated website for staying on top of the AI space across three categories:

1. **Announcements** — first-party news from major AI companies
2. **GitHub projects** — interesting new/rising AI repos (agents, skills, MCP, automated workflows)
3. **Research** — relevant papers newly submitted to arxiv

A scheduled pipeline searches, vets (heuristics only — no LLM calls, no API cost), and aggregates items into one JSON file per day. A zero-build static site renders the digest with a browsable archive of previous days.

## Decisions

| Decision | Choice |
|---|---|
| Hosting / runtime | GitHub Actions (daily cron) + GitHub Pages |
| Vetting | Heuristics only (keywords, stars, recency, source reputation) |
| News sources | Official company blogs only |
| GitHub discovery | New repos + rising repos |
| Arxiv scope | cs.AI, cs.CL, cs.LG |
| Site UX | Daily digest landing page + date-picker archive |
| Stack | Python pipeline; plain HTML/CSS/JS site (no framework, no build step) |

## Repo layout

```
pipeline/                  Python package — the daily job
  config.yaml              source list, keywords, thresholds (all tuning lives here)
  fetch_news.py            RSS/Atom adapters + minimal HTML scrapers
  fetch_github.py          GitHub search API queries
  fetch_arxiv.py           arxiv API query
  vetting.py               scoring heuristics
  aggregate.py             dedupe, rank, write daily JSON + index
  __main__.py              CLI entry: python -m pipeline
site/                      the website, served by GitHub Pages
  index.html
  app.js
  style.css
  data/
    YYYY-MM-DD.json        one digest per day (committed by the workflow)
    index.json             list of available dates
state/
  seen.json                canonical IDs already surfaced → first-seen date
tests/                     pytest; fixture-based, no live network
.github/workflows/daily.yml
```

## Category 1: Announcements

- Config-driven source list. Initial set: OpenAI, Google AI / DeepMind, Microsoft, Meta AI, Apple ML Research, Hugging Face, Mistral, xAI, Anthropic. Exact feed URLs verified during implementation.
- Each source has an adapter type: `rss` (feedparser) or `scrape` (small HTML parser) for sources without feeds (notably Anthropic's newsroom).
- Broad company blogs (e.g. Microsoft) are keyword-filtered to AI-relevant posts; dedicated AI blogs pass through unfiltered.
- Window: posts published in the last 3 days (lookback catches missed runs); deduped by canonical URL against `state/seen.json` so an item appears on exactly one day.

## Category 2: GitHub projects

Two searches per run via the GitHub search API (uses the free `GITHUB_TOKEN` provided to Actions):

- **Brand-new:** created in the last 7 days, ≥15 stars, matching AI-agent/skills/MCP/workflow/LLM topics and keywords.
- **Rising:** created in the last 60 days, ≥200 stars, same topic/keyword match.

Score = log(stars) + keyword matches in name/description/topics. Repos already in `seen.json` are skipped. Thresholds and keyword lists live in `config.yaml`.

## Category 3: Research

- Arxiv API query: papers submitted in the last 1 day to cs.AI, cs.CL, or cs.LG.
- Score = keyword hits in title/abstract (LLM, agent, reasoning, benchmark, fine-tuning, RLHF, multimodal, …; list in `config.yaml`).
- Top ~30 papers above the score threshold make the digest; deduped by arxiv ID.

## Data schema

`site/data/YYYY-MM-DD.json`:

```json
{
  "date": "2026-07-10",
  "generated_at": "2026-07-10T13:02:11Z",
  "errors": [{"source": "mistral", "message": "HTTP 503"}],
  "categories": {
    "announcements": [
      {"id": "<canonical url>", "title": "...", "url": "...", "source": "openai",
       "published": "...", "snippet": "...", "score": 3.2, "signals": ["keyword:model"]}
    ],
    "github": [
      {"id": "owner/repo", "title": "owner/repo", "url": "...", "description": "...",
       "stars": 412, "language": "Python", "topics": ["mcp", "agents"],
       "created_at": "...", "score": 8.1, "signals": ["rising", "keyword:agent"]}
    ],
    "research": [
      {"id": "2407.01234", "title": "...", "url": "https://arxiv.org/abs/...",
       "authors": ["..."], "snippet": "<abstract excerpt>", "categories": ["cs.AI"],
       "published": "...", "score": 4.0, "signals": ["keyword:reasoning"]}
    ]
  }
}
```

`site/data/index.json`: `["2026-07-10", "2026-07-09", ...]` (newest first).

## Website

- Plain HTML/CSS/JS; fetches `index.json`, defaults to the newest date, date picker for the archive.
- Three sections (Announcements / GitHub / Research) of item cards: linked title, source badge, timestamp, snippet, signals (stars, matched keywords).
- Shows a notice for any source listed in that day's `errors`.
- Light/dark theme via `prefers-color-scheme`.

## Automation

`.github/workflows/daily.yml`:

- Triggers: daily cron (~13:00 UTC) + `workflow_dispatch`.
- Steps: checkout → setup Python → run pipeline → commit `site/data/` and `state/seen.json` → deploy `site/` to GitHub Pages (Pages artifact flow).

## Error handling

- Each source fetch is isolated: failure is logged, recorded in the day's `errors` array, and never aborts the run.
- Transient HTTP errors retried with backoff.
- The run fails only if *all* sources fail (nothing to publish).

## Testing

- Pytest unit tests for vetting/scoring, filtering, and dedupe with fixture data.
- Fetchers tested against recorded sample responses (saved fixtures); no live network in CI tests.

## Out of scope (YAGNI)

- LLM-based summarization or ranking
- Tech-press sources, comments/social signals
- Search within the site, user accounts, notifications
