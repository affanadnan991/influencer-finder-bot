"""A lightweight discovery engine for Instagram profiles via following list."""

from __future__ import annotations

import os
import random
import re
import time
from datetime import datetime
from typing import Any, Optional

from config import BROWSER_DELAY, HEADLESS, INSTAGRAM_SESSION_FILE, TIMEOUT
from discovery_engine.relevance import keyword_matches, score_profile
from storage import ProfileStore


_PROFILE_LINK_EXCLUDED = {
    "about", "accounts", "direct", "directory", "explore", "graphql",
    "p", "press", "reel", "reels", "stories", "tv", "followers", "following",
    "login", "signup", "emails", "settings", "nametag", "session",
    "developer", "legal", "privacy", "terms", "help",
}


class DiscoveryEngine:
    """Run keyword discovery on a target's following list."""

    def __init__(
        self,
        target: str,
        keywords: list[str],
        store: Optional[ProfileStore] = None,
        progress_callback: Optional[Any] = None,
    ):
        self.target = target.strip().lower().lstrip("@")
        self.keywords = [k.strip() for k in keywords if k.strip()][:7]
        self.store = store or ProfileStore()
        self.progress_callback = progress_callback
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.counters: dict[str, int] = {
            "followings_found": 0,
            "profiles_checked": 0,
            "keyword_matches": 0,
            "profiles_saved": 0,
            "profiles_skipped": 0,
            "bio_extract_failed": 0,
            "errors": 0,
        }

    # ── Browser ────────────────────────────────────────────────────

    def setup_browser(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=HEADLESS,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context_args = {
                "viewport": {"width": 1280, "height": 720},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            }
            if os.path.exists(INSTAGRAM_SESSION_FILE):
                context_args["storage_state"] = INSTAGRAM_SESSION_FILE
            self.context = self.browser.new_context(**context_args)
            self.page = self.context.new_page()
            self._log("Browser started")
            return True
        except Exception as exc:
            self.counters["errors"] += 1
            self._log(f"Browser start FAILED: {exc}")
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

    # ── Main Discovery Flow ────────────────────────────────────────

    def discover(self, max_following: int = 200) -> list[dict[str, Any]]:
        kw_display = ", ".join(self.keywords) if self.keywords else "(no keywords — collect ALL)"
        print(f"\n{'='*60}")
        print(f"  Target:   @{self.target}")
        print(f"  Keywords: {kw_display}")
        print(f"  Max Following: {max_following}")
        print(f"{'='*60}\n")

        if not self.setup_browser():
            print("ERROR: Browser start nahi hua!")
            return []

        try:
            # Step 1: Collect followings
            print("--- Step 1: Collecting following list ---")
            self._report_progress("collecting", "Opening following list...")
            followings = self._collect_following(self.target, max_following=max_following)
            if not followings:
                print("\nERROR: Following list nahi mili!")
                print("  Possible reasons:")
                print("  1. instagram_session.json expired — cookies refresh karo")
                print("  2. Profile private hai")
                print("  3. Instagram ne bot detect kar lia — thodi der baad try karo")
                return []

            self.counters["followings_found"] = len(followings)
            print(f"\nTotal followings collected: {len(followings)}")
            self._report_progress("checking", f"Found {len(followings)} followings")

            # Step 2: Check each following
            print(f"\n--- Step 2: Checking {len(followings)} profiles ---\n")
            discovered: list[dict[str, Any]] = []

            for i, username in enumerate(followings, 1):
                print(f"[{i}/{len(followings)}] @{username}", end=" ")
                self.counters["profiles_checked"] += 1
                self._report_progress("checking", f"[{i}/{len(followings)}] @{username}")

                bio = self._get_profile_bio(username)
                if bio is None:
                    self.counters["bio_extract_failed"] += 1
                    print("-> bio failed, skip")
                    continue

                profile = {
                    "username": username,
                    "profile_url": f"https://www.instagram.com/{username}/",
                    "bio": bio,
                }

                # No keywords = save ALL with non-empty bio
                if not self.keywords:
                    if bio.strip():
                        profile["score"] = 0
                        profile["niche"] = ""
                        profile["date_collected"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        discovered.append(profile)
                        self.counters["profiles_saved"] += 1
                        print("-> SAVED (no keyword filter)")
                    else:
                        self.counters["profiles_skipped"] += 1
                        print("-> empty bio, skip")
                    continue

                # Check keywords in bio
                matched_kw = keyword_matches(profile, self.keywords)
                if matched_kw:
                    score = score_profile(profile, self.keywords)
                    profile["score"] = score
                    profile["niche"] = matched_kw
                    profile["date_collected"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    discovered.append(profile)
                    self.counters["keyword_matches"] += 1
                    self.counters["profiles_saved"] += 1
                    print(f'-> MATCH! "{matched_kw}" (score: {score})')
                else:
                    self.counters["profiles_skipped"] += 1
                    print("-> no match")

            # Step 3: Save
            if discovered:
                filepath = self.store.save_results(discovered)
                print(f"\n{'='*60}")
                print(f"  DONE! {len(discovered)} profiles saved to {filepath}")
                print(f"{'='*60}")
            else:
                filepath = ""
                print(f"\n{'='*60}")
                print(f"  DONE! No matching profiles found.")
                print(f"{'='*60}")

            self._report_progress("done", f"{len(discovered)} profiles saved")
            return discovered
        finally:
            self.close_browser()

    # ── Bio Extraction ─────────────────────────────────────────────

    def _get_profile_bio(self, username: str) -> Optional[str]:
        if not self.page:
            return None
        url = f"https://www.instagram.com/{username}/"
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
        except Exception:
            self.counters["errors"] += 1
            return None
        time.sleep(BROWSER_DELAY + random.uniform(0.2, 0.6))
        html = self.page.content()
        return self._extract_bio_from_html(html)

    @staticmethod
    def _extract_bio_from_html(html: str) -> Optional[str]:
        patterns = [
            r'"biography":"((?:[^"\\]|\\.)*)"',
            r'"biography"\s*:\s*"((?:[^"\\]|\\.)*)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                bio = match.group(1)
                bio = bio.replace('\\u0026', '&').replace('\\n', ' ').replace('\\/', '/')
                bio = re.sub(r'\\u[0-9a-fA-F]{4}', '', bio)
                bio = re.sub(r'\s+', ' ', bio).strip()
                return bio
        return None

    # ── Following List ─────────────────────────────────────────────

    def _collect_following(self, target: str, max_following: int = 200) -> list[str]:
        if not self._open_following_dialog(target):
            return []
        followings = self._harvest_from_dialog(target, max_following)
        self._log(f"Harvested {len(followings)} followings from @{target}")
        return followings

    def _open_following_dialog(self, target: str) -> bool:
        """Go to profile page, click "following" count, wait for dialog."""
        if not self.page:
            return False

        # Step 1: Navigate to profile page
        profile_url = f"https://www.instagram.com/{target}/"
        self._log(f"Opening profile page: {profile_url}")
        try:
            self.page.goto(profile_url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
        except Exception as exc:
            self.counters["errors"] += 1
            self._log(f"Failed to load profile: {exc}")
            return False
        time.sleep(BROWSER_DELAY + random.uniform(0.5, 1.0))

        # Step 2: Click on "following" count — try multiple strategies
        dialog_opened = False

        # ── Strategy A: Find <a> with href containing /following ──
        self._log("Strategy A: Looking for <a> with href /following ...")
        strategy_a_selectors = [
            f'a[href="/{target}/following/"]',
            f'a[href="/{target}/following"]',
            'a[href*="/following"]',
        ]
        for sel in strategy_a_selectors:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=2000):
                    loc.click(timeout=5000)
                    self._log(f"  Clicked: {sel}")
                    time.sleep(BROWSER_DELAY + 1)
                    if self._verify_following_dialog():
                        dialog_opened = True
                        break
            except Exception:
                continue

        # ── Strategy B: Use JavaScript to find the following link ──
        if not dialog_opened:
            self._log("Strategy B: Using JavaScript to find following link ...")
            try:
                clicked = self.page.evaluate(f"""() => {{
                    // Look through all <a> tags
                    const links = document.querySelectorAll('a');
                    for (const link of links) {{
                        const href = link.getAttribute('href') || '';
                        // Must contain /following and be the stats link (not nav)
                        if (href.includes('/{target}/following')) {{
                            link.click();
                            return 'href_match';
                        }}
                    }}
                    return false;
                }}""")
                if clicked:
                    self._log(f"  JS clicked via: {clicked}")
                    time.sleep(BROWSER_DELAY + 1.5)
                    if self._verify_following_dialog():
                        dialog_opened = True
            except Exception as exc:
                self._log(f"  JS click failed: {exc}")

        # ── Strategy C: Find "following" text in the header/stats area ──
        if not dialog_opened:
            self._log("Strategy C: Looking for 'following' text in stats ...")
            try:
                # Instagram stats section usually has: posts, followers, following
                # Find element with text "following" and click its parent <a>
                clicked = self.page.evaluate("""() => {
                    // Find all elements
                    const walker = document.createTreeWalker(
                        document.body, NodeFilter.SHOW_TEXT, null, false
                    );
                    while (walker.nextNode()) {
                        const node = walker.currentNode;
                        const text = node.textContent.trim().toLowerCase();
                        if (text === 'following' || text.endsWith(' following')) {
                            // Walk up to find clickable parent
                            let el = node.parentElement;
                            for (let i = 0; i < 5; i++) {
                                if (!el) break;
                                if (el.tagName === 'A' || el.onclick || el.getAttribute('role') === 'link') {
                                    el.click();
                                    return 'text_found';
                                }
                                el = el.parentElement;
                            }
                            // Just click the text's parent
                            if (node.parentElement) {
                                node.parentElement.click();
                                return 'text_parent_click';
                            }
                        }
                    }
                    return false;
                }""")
                if clicked:
                    self._log(f"  Clicked via: {clicked}")
                    time.sleep(BROWSER_DELAY + 1.5)
                    if self._verify_following_dialog():
                        dialog_opened = True
            except Exception as exc:
                self._log(f"  Text search failed: {exc}")

        # ── Strategy D: Playwright getByRole/getByText ──
        if not dialog_opened:
            self._log("Strategy D: Playwright text locator ...")
            try:
                # Try clicking on text that looks like "XXX following"
                loc = self.page.get_by_role("link", name=re.compile(r"following", re.IGNORECASE)).first
                loc.click(timeout=5000)
                self._log("  Clicked via getByRole link 'following'")
                time.sleep(BROWSER_DELAY + 1.5)
                if self._verify_following_dialog():
                    dialog_opened = True
            except Exception:
                pass

        if not dialog_opened:
            try:
                loc = self.page.locator("text=/\\d+\\s*following/i").first
                loc.click(timeout=5000)
                self._log("  Clicked via regex 'NNN following'")
                time.sleep(BROWSER_DELAY + 1.5)
                if self._verify_following_dialog():
                    dialog_opened = True
            except Exception:
                pass

        # ── Strategy E: Direct URL as last resort ──
        if not dialog_opened:
            self._log("Strategy E: Direct URL /following/ ...")
            try:
                self.page.goto(
                    f"https://www.instagram.com/{target}/following/",
                    wait_until="domcontentloaded",
                    timeout=TIMEOUT * 1000,
                )
                time.sleep(BROWSER_DELAY + 2)
                if self._verify_following_dialog():
                    dialog_opened = True
                    self._log("  Dialog opened via direct URL")
            except Exception as exc:
                self._log(f"  Direct URL failed: {exc}")

        if dialog_opened:
            self._log("Following dialog opened successfully!")
        else:
            self.counters["errors"] += 1
            self._log("ALL strategies FAILED to open following dialog")

        return dialog_opened

    def _verify_following_dialog(self) -> bool:
        """Check if the following dialog is actually open with real user list."""
        if not self.page:
            return False

        try:
            # Must have a dialog
            dialog = self.page.query_selector('div[role="dialog"]')
            if not dialog:
                self._log("  (verify) No dialog found")
                return False

            # Dialog must contain profile links (not just random links)
            dialog_html = dialog.inner_html()
            profile_links = re.findall(r'href="/([a-zA-Z0-9._]{1,30})/"', dialog_html)
            filtered = [u for u in profile_links if u.lower() not in _PROFILE_LINK_EXCLUDED]

            if len(filtered) >= 1:
                self._log(f"  (verify) Dialog has {len(filtered)} profile links — VALID")
                return True
            else:
                self._log(f"  (verify) Dialog has {len(filtered)} profile links — NOT a user list")
                return False
        except Exception as exc:
            self._log(f"  (verify) Error: {exc}")
            return False

    def _harvest_from_dialog(self, target: str, max_following: int = 200) -> list[str]:
        """Scroll the following dialog using mouse wheel and extract usernames."""
        if not self.page:
            return []

        target_lower = target.lower()
        collected: dict[str, None] = {}
        stagnant = 0

        # First, find the dialog and get its bounding box for mouse wheel scrolling
        dialog = self.page.query_selector('div[role="dialog"]')
        if not dialog:
            self._log("No dialog found for harvesting")
            return []

        dialog_box = dialog.bounding_box()
        if not dialog_box:
            self._log("Could not get dialog bounding box")
            return []

        # Center point of the dialog for mouse wheel
        cx = dialog_box['x'] + dialog_box['width'] / 2
        cy = dialog_box['y'] + dialog_box['height'] / 2

        # Move mouse to dialog center first
        self.page.mouse.move(cx, cy)

        for scroll_num in range(200):  # max 200 scroll attempts
            prev_count = len(collected)

            # Extract usernames from dialog
            try:
                dialog_html = dialog.inner_html()
            except Exception:
                # Dialog might have been replaced — re-find it
                dialog = self.page.query_selector('div[role="dialog"]')
                if not dialog:
                    break
                try:
                    dialog_html = dialog.inner_html()
                except Exception:
                    break

            for m in re.findall(r'href="/([a-zA-Z0-9._]{1,30})/"', dialog_html):
                username = m.lower()
                if username in _PROFILE_LINK_EXCLUDED or username == target_lower:
                    continue
                collected.setdefault(username, None)

            if len(collected) >= max_following:
                self._log(f"Reached max_following limit ({max_following})")
                break

            if len(collected) == prev_count:
                stagnant += 1
                if stagnant >= 8:
                    self._log(f"Scrolling stopped — no new users after {stagnant} scrolls")
                    break
            else:
                stagnant = 0

            # ── Scroll using mouse wheel (most reliable) ──
            self.page.mouse.wheel(0, 600)

            # ── Also try JS scroll on scrollable elements inside dialog ──
            try:
                self.page.evaluate("""() => {
                    const dialog = document.querySelector('div[role="dialog"]');
                    if (!dialog) return;
                    const divs = dialog.querySelectorAll('div');
                    for (const div of divs) {
                        if (div.scrollHeight > div.clientHeight + 20) {
                            div.scrollTop = div.scrollHeight;
                        }
                    }
                }""")
            except Exception:
                pass

            time.sleep(BROWSER_DELAY / 2 + random.uniform(0.2, 0.6))

            # Progress updates
            if (scroll_num + 1) % 15 == 0:
                self._log(f"...scrolled {scroll_num+1}x ({len(collected)} usernames)")

        result = list(collected.keys())[:max_following]
        return result

    # ── Helpers ────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        print(f"  >> {msg}")

    def _report_progress(self, phase: str, detail: str = "") -> None:
        """Report progress to the callback if set."""
        if self.progress_callback:
            self.progress_callback(
                phase=phase,
                detail=detail,
                counters=dict(self.counters),
            )

    def get_report(self) -> dict[str, Any]:
        return {"counters": dict(self.counters)}
