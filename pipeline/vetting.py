"""Heuristic scoring: keyword matching and popularity-based scores."""

import math
import re


def keyword_matches(text, keywords):
    """Return keywords appearing in text as whole words, case-insensitive."""
    if not text:
        return []
    lowered = text.lower()
    matches = []
    for keyword in keywords:
        pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"
        if re.search(pattern, lowered):
            matches.append(keyword)
    return matches


def score_repo(stars, matches):
    """Popularity (log-scaled stars) plus topical relevance (keyword hits)."""
    return round(math.log2(stars + 1) + len(matches), 2)


def score_paper(matches):
    return float(len(matches))
