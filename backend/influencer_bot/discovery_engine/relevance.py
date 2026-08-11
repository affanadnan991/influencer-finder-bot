"""Multi-keyword matching for Instagram profile bios."""

from __future__ import annotations

import re
from typing import Optional


def normalize_keyword(keyword: Optional[str]) -> str:
    if not keyword:
        return ""
    return re.sub(r"\s+", " ", str(keyword).strip().lower())


def build_keyword_variants(keyword: Optional[str]) -> list[str]:
    """Build all search variants for a keyword.

    Example: "food blogger" → ["food blogger", "foodblogger", "food-blogger",
                                "food_blogger", "food", "blogger"]
    """
    base = normalize_keyword(keyword)
    if not base:
        return []
    parts = [p for p in re.split(r"[^a-z0-9]+", base) if p]
    if not parts:
        return [base]

    variants = {base}
    if len(parts) > 1:
        variants.add(" ".join(parts))
        variants.add("".join(parts))
        variants.add("-".join(parts))
        variants.add("_".join(parts))
        for part in parts:
            variants.add(part)
    else:
        variants.add(parts[0])

    return sorted(variants)


def keyword_matches(profile: dict, keywords: list[str]) -> Optional[str]:
    """Check if ANY keyword from the list matches in the profile's bio.

    Returns the first matched keyword string, or None if no match.
    Case-insensitive. Checks all variant forms of each keyword.
    """
    if not profile or not keywords:
        return None

    bio = str(profile.get("bio") or "").lower().strip()
    if not bio:
        return None

    for keyword in keywords:
        variants = build_keyword_variants(keyword)
        for variant in variants:
            if variant and variant in bio:
                return keyword  # return original keyword that matched
    return None


def score_profile(profile: dict, keywords: list[str]) -> int:
    """Score how well a profile matches the keywords. Higher = better."""
    if not profile or not keywords:
        return 0

    bio = str(profile.get("bio") or "").lower().strip()
    if not bio:
        return 0

    score = 0
    for keyword in keywords:
        variants = build_keyword_variants(keyword)
        for variant in variants:
            if not variant:
                continue
            if variant in bio:
                score += 3

    return score
