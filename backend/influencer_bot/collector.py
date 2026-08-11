"""Dedicated collection engine for ingesting Instagram profiles from a supplied page URL."""

from __future__ import annotations

import os
import random
import time
from datetime import datetime
from typing import Any, Optional

from config import BROWSER_DELAY, HEADLESS, INSTAGRAM_SESSION_FILE, TIMEOUT
from utils import extract_instagram_username, normalize_url
from storage import ProfileStore


def build_collection_record(
    username: Optional[str] = None,
    profile_url: Optional[str] = None,
    followers: Optional[int] = None,
    following: Optional[int] = None,
    bio: Optional[str] = None,
    verified: Optional[bool] = None,
    source_url: Optional[str] = None,
) -> dict[str, Any]:
    """Build a raw collection record with only ingestion fields."""
    normalized_url = normalize_url(profile_url or username or "")
    if not normalized_url:
        return {}

    cleaned_username = extract_instagram_username(normalized_url)
    if not cleaned_username:
        return {}

    cleaned_bio = " ".join(str(bio or "").split()).strip() if bio is not None else None
    if cleaned_bio and len(cleaned_bio) > 220:
        cleaned_bio = cleaned_bio[:220]

    return {
        "username": cleaned_username,
        "profile_url": normalized_url,
        "followers": followers,
        "following": following,
        "bio": cleaned_bio,
        "verified": bool(verified) if verified is not None else None,
        "source_url": source_url or "",
        "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


class InstagramCollector:
    """Collect Instagram profiles from a supplied page URL with no filtering."""

    def __init__(self, page_url: Optional[str] = None, store: Optional[ProfileStore] = None):
        self.page_url = page_url
        self.store = store or ProfileStore()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.collected_profiles: list[dict[str, Any]] = []

    def setup_browser(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=HEADLESS, args=["--disable-blink-features=AutomationControlled"])
            context_args = {
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            if os.path.exists(INSTAGRAM_SESSION_FILE):
                context_args["storage_state"] = INSTAGRAM_SESSION_FILE
            self.context = self.browser.new_context(**context_args)
            self.page = self.context.new_page()
            return True
        except Exception:
            return False

    def close_browser(self) -> None:
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass

    def _scroll_page(self, max_scrolls: int = 20, delay: float = 0.4) -> None:
        if not self.page:
            return

        last_count = 0
        for _ in range(max_scrolls):
            self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(delay + random.uniform(0.1, 0.3))
            current_count = len(self._extract_visible_profiles())
            if current_count == last_count:
                break
            last_count = current_count

    def _extract_visible_profiles(self) -> list[dict[str, Any]]:
        if not self.page:
            return []
        html = self.page.content()
        profiles = []
        for match in __import__("re").findall(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._-]+)/?', html, flags=__import__("re").IGNORECASE):
            username = match.lower()
            if username in {"about", "accounts", "direct", "directory", "explore", "graphql", "p", "press", "reel", "reels", "stories", "tv"}:
                continue
            profile = build_collection_record(username=username, profile_url=f"https://www.instagram.com/{username}/", source_url=self.page_url or "")
            if profile:
                profiles.append(profile)
        return profiles

    def collect(self, page_url: Optional[str] = None, max_scrolls: int = 20, limit: Optional[int] = None) -> list[dict[str, Any]]:
        target_url = page_url or self.page_url
        if not target_url:
            return []

        if not self.setup_browser():
            return []

        try:
            self.page.goto(target_url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
            self._scroll_page(max_scrolls=max_scrolls)
            profiles = self._extract_visible_profiles()
            if limit is not None:
                profiles = profiles[:limit]

            self.collected_profiles = profiles
            if profiles:
                self.store.append_profiles(profiles)
            return profiles
        finally:
            self.close_browser()
