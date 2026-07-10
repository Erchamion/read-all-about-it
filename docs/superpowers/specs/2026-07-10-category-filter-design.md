# Category Filter Tabs — Digest Site

**Date:** 2026-07-10
**Status:** Approved

## Purpose

Let the user view one digest category at a time. A tab bar filters the existing three sections; grouping within sections is unchanged.

## Design

- `site/index.html`: add `<nav id="filter" aria-label="Category filter">` between the header and `<main>`, containing four `<button>` elements with `data-filter` values `all`, `announcements`, `github`, `research`. Labels: "All", "📣 Announcements", "🐙 GitHub", "📄 Research". Each button contains a `<span class="count">` (empty for All) filled at render time.
- `site/app.js`:
  - `applyFilter(name)`: toggles a `hidden` class on the three `<section>`s (`all` shows every section), sets `aria-pressed`/`active` class on the matching button, and updates `location.hash` (empty hash for `all`, `#github` etc. otherwise) without adding history entries (`history.replaceState`).
  - On load: read `location.hash`; if it names a category use it, otherwise default to `all`. Unknown hashes fall back to `all`.
  - On each `render(digest)`: update each tab's count span with that category's item count for the displayed date.
  - Filter state persists across date switches (render does not reset the filter).
- `site/style.css`: pill-style buttons using the existing CSS variables (`--card`, `--border`, `--accent`, `--muted`); active tab uses `--accent` border/text. `.hidden { display: none; }`.

## Out of scope (YAGNI)

- Sub-grouping within sections (by company / repo mode / arxiv category)
- localStorage persistence (URL hash covers refresh/bookmark)
- Pipeline or data-schema changes — none needed

## Error handling

No new failure modes: notices render above the sections and remain visible under every filter. Empty categories keep the existing "Nothing today." message.

## Testing

No JS test framework exists (accepted for this static site). Verify with `node --check site/app.js`, serving locally (`python3 -m http.server`) with curl checks for asset integrity, and static cross-checks that every id/class referenced in JS exists in the HTML. Visual confirmation on the live site after deploy.
