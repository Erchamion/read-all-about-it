"""Discover new and rising AI repos via the GitHub search API."""

import os
import time
from datetime import timedelta

import requests

from .vetting import keyword_matches, score_repo

API_URL = "https://api.github.com/search/repositories"
MODES = ("new", "rising")


def default_fetcher(params):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "read-all-about-it/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    time.sleep(2)  # stay under the search API rate limit
    return response.json()


def _repo_item(raw, mode, repo_keywords):
    text = " ".join(
        [raw.get("name") or "", raw.get("description") or "", " ".join(raw.get("topics", []))]
    )
    matches = keyword_matches(text, repo_keywords)
    stars = raw.get("stargazers_count", 0)
    return {
        "id": raw["full_name"],
        "title": raw["full_name"],
        "url": raw["html_url"],
        "description": (raw.get("description") or "")[:300],
        "stars": stars,
        "language": raw.get("language"),
        "topics": raw.get("topics", [])[:8],
        "created_at": raw.get("created_at"),
        "score": score_repo(stars, matches),
        "signals": [mode] + [f"keyword:{m}" for m in matches],
    }


def fetch_github(config, now, fetcher=default_fetcher):
    items, errors = [], []
    seen_names = set()
    for mode in MODES:
        mode_config = config[mode]
        cutoff = (now - timedelta(days=mode_config["created_within_days"])).date().isoformat()
        for term in config["search_terms"]:
            query = f'"{term}" created:>={cutoff} stars:>={mode_config["min_stars"]}'
            try:
                data = fetcher(
                    {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": config["per_query_limit"],
                    }
                )
            except Exception as error:
                errors.append({"source": f"github:{mode}:{term}", "message": str(error)})
                continue
            for raw in data.get("items", []):
                if raw["full_name"] in seen_names:
                    continue
                seen_names.add(raw["full_name"])
                items.append(_repo_item(raw, mode, config["repo_keywords"]))
    return items, errors
