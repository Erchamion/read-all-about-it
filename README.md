# Read All About It

A daily AI digest: company announcements, notable GitHub AI projects, and
arxiv research, aggregated by a heuristic pipeline and browsable as a static
site with a per-day archive.

## How it works

- `pipeline/` fetches official company blogs (RSS or scraped), searches
  GitHub for new/rising AI-agent repos, and pulls recent cs.AI/cs.CL/cs.LG
  papers from arxiv. Items are keyword/popularity scored, deduped against
  `state/seen.json`, and written to `site/data/<date>.json`.
- `site/` is a zero-build static page that renders the JSON with a date picker.
- `.github/workflows/daily.yml` runs the pipeline daily at 13:00 UTC, commits
  the data, and deploys `site/` to GitHub Pages.

## Local usage

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest                              # tests (no network)
.venv/bin/python scripts/check_sources.py     # live-check news sources
.venv/bin/python -m pipeline                  # produce today's digest
cd site && python3 -m http.server 8123        # browse at localhost:8123
```

All tuning — sources, keywords, star thresholds, paper caps — lives in
`pipeline/config.yaml`.
