# Category Filter Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Filter tabs (All / Announcements / GitHub / Research) on the digest site, with URL-hash persistence and per-tab item counts.

**Architecture:** Pure client-side change to the three existing site files. A `<nav>` of pill buttons toggles a `hidden` class on the existing sections; `location.hash` (via `history.replaceState`) persists the choice; `render()` fills per-tab counts each time a digest loads.

**Tech Stack:** Vanilla HTML/CSS/JS (no build step, no framework — matches the existing site).

**Spec:** `docs/superpowers/specs/2026-07-10-category-filter-design.md`

## Global Constraints

- Only `site/index.html`, `site/app.js`, `site/style.css` change. No pipeline, data, or workflow changes.
- The site must remain fully self-contained (no external resources) and XSS-safe (all dynamic text via `textContent`).
- app.js was patched after its original version (date-switch try/catch; http(s)-only links) — **Read the current files first and add to them; do not regenerate any file from scratch.**
- Filter state persists across date switches; unknown hashes fall back to `all`; `history.replaceState` only (no history entries).
- Match the existing code style (the `el()` helper, CSS variables, no semicolon-free style drift).
- Commit messages: conventional style.

---

### Task 1: Filter tabs

**Files:**
- Modify: `site/index.html` (insert nav between `</header>` and `<main>`)
- Modify: `site/app.js` (two new functions; additions to `render()` and `init()`)
- Modify: `site/style.css` (pill styles + `.hidden`)

**Interfaces:**
- Consumes: existing `SECTIONS` array (`["announcements", "github", "research"]`), `el()` helper, section ids `#announcements/#github/#research`, `render(digest)`, `init()`.
- Produces: `applyFilter(name: string)` and `currentFilter(): string` in app.js; `<nav id="filter">` with `button[data-filter]` elements; `.hidden` utility class. (Nothing else will consume these — this is a leaf feature.)

- [ ] **Step 1: Add the nav to index.html**

Insert between `</header>` and `<main>`:

```html
  <nav id="filter" aria-label="Category filter">
    <button data-filter="all" aria-pressed="true">All</button>
    <button data-filter="announcements" aria-pressed="false">📣 Announcements <span class="count"></span></button>
    <button data-filter="github" aria-pressed="false">🐙 GitHub <span class="count"></span></button>
    <button data-filter="research" aria-pressed="false">📄 Research <span class="count"></span></button>
  </nav>
```

- [ ] **Step 2: Add filter logic to app.js**

Add these two functions after the existing `el()` helper:

```javascript
function currentFilter() {
  const name = location.hash.slice(1);
  return SECTIONS.includes(name) ? name : "all";
}

function applyFilter(name) {
  for (const button of document.querySelectorAll("#filter button")) {
    const active = button.dataset.filter === name;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  }
  for (const section of SECTIONS) {
    const hidden = name !== "all" && name !== section;
    document.getElementById(section).classList.toggle("hidden", hidden);
  }
  const url = name === "all" ? location.pathname + location.search : `#${name}`;
  history.replaceState(null, "", url);
}
```

At the top of the existing `render(digest)` function body, add the count update:

```javascript
  for (const name of SECTIONS) {
    const count = (digest.categories[name] || []).length;
    document.querySelector(`#filter button[data-filter="${name}"] .count`).textContent = String(count);
  }
```

In the existing `init()`, immediately before the `try {` line, wire the buttons and initial state:

```javascript
  for (const button of document.querySelectorAll("#filter button")) {
    button.addEventListener("click", () => applyFilter(button.dataset.filter));
  }
  applyFilter(currentFilter());
```

Do not modify the existing date-picker listener, its try/catch, or `itemCard`.

- [ ] **Step 3: Add styles to style.css**

Append:

```css
#filter {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}

#filter button {
  padding: 0.35rem 0.9rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  color: var(--fg);
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
}

#filter button:hover { border-color: var(--accent); }

#filter button.active {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

#filter .count {
  color: var(--muted);
  font-size: 0.8rem;
}

.hidden { display: none; }
```

- [ ] **Step 4: Verify headlessly**

Run (from repo root):

```bash
node --check site/app.js
python3 - <<'EOF'
import re
html = open("site/index.html").read()
js = open("site/app.js").read()
css = open("site/style.css").read()
assert 'id="filter"' in html and html.count("data-filter") == 4
assert html.index("</header>") < html.index('id="filter"') < html.index("<main>")
assert "function applyFilter" in js and "function currentFilter" in js
assert "history.replaceState" in js and "hashchange" not in js
assert js.count("addEventListener") >= 2  # date picker + filter buttons
assert ".hidden { display: none; }" in css and "#filter button.active" in css
# every data-filter value except "all" is a real section id
for name in re.findall(r'data-filter="(\w+)"', html):
    assert name == "all" or f'id="{name}"' in html, name
print("static checks ok")
EOF
(cd site && python3 -m http.server 8124 &>/dev/null &) && sleep 1 \
  && for f in "" app.js style.css data/index.json; do \
       curl -s -o /dev/null -w "/$f %{http_code}\n" "http://localhost:8124/$f"; done \
  && kill %1
```

Expected: `static checks ok` and four `200`s. Also run `.venv/bin/pytest -q` once (should be 37 passed — confirms nothing outside `site/` broke).

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/app.js site/style.css
git commit -m "feat: category filter tabs with hash persistence and counts"
```

---

### Task 2: Deploy and verify live

**Files:** none (operations only).

**Interfaces:**
- Consumes: Task 1's commit on `main`; existing `daily.yml` workflow (deploys `site/` to Pages; same-day pipeline reruns are idempotent by design, so re-triggering is safe).
- Produces: updated live site.

- [ ] **Step 1: Push and trigger the deploy**

```bash
git push
gh workflow run daily.yml
sleep 10 && gh run watch "$(gh run list --workflow=daily.yml --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
```

Expected: run completes green (build + deploy jobs).

- [ ] **Step 2: Verify the live site**

```bash
curl -s https://erchamion.github.io/read-all-about-it/ | grep -c 'data-filter'
curl -s -o /dev/null -w "%{http_code}\n" https://erchamion.github.io/read-all-about-it/app.js
```

Expected: `4` and `200`. (Pages CDN may cache for a minute or two — retry once after 60s before treating a stale response as a failure.) Then confirm visually in a browser: tabs render, clicking GitHub shows only that section with its count, URL shows `#github`, refresh keeps the filter, date picker keeps the filter active.

---

## Self-Review Notes

- Spec coverage: nav (Task 1 Step 1), applyFilter/hash/counts (Step 2), styles (Step 3), no-new-error-modes + persistence across date switches (Step 2: render doesn't touch filter state), testing section (Step 4), deploy (Task 2). No gaps.
- Placeholder scan: clean — all code complete.
- Consistency: `applyFilter`/`currentFilter` names match between Steps 2 and 4's static checks; `data-filter` values match `SECTIONS` entries.
