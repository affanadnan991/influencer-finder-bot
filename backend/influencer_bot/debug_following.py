"""Debug script: Opens target's following list and dumps what the bot actually sees.

Usage: python debug_following.py --target "glowzwith_nina"

This will:
1. Open the following page
2. Take a screenshot (output/debug_screenshot.png)
3. Dump the dialog HTML (output/debug_dialog.html)
4. Try all scroll methods and report which ones work
5. Show all usernames it can find
"""

import argparse
import os
import re
import time
import random

from config import BROWSER_DELAY, HEADLESS, INSTAGRAM_SESSION_FILE, TIMEOUT, OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(description="Debug the following list extraction")
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    target = args.target.strip().lower().lstrip("@")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    ctx_args = {
        "viewport": {"width": 1280, "height": 720},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    if os.path.exists(INSTAGRAM_SESSION_FILE):
        ctx_args["storage_state"] = INSTAGRAM_SESSION_FILE
    context = browser.new_context(**ctx_args)
    page = context.new_page()

    # Step 1: Navigate to /following/
    url = f"https://www.instagram.com/{target}/following/"
    print(f"\n[1] Navigating to {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
    time.sleep(4)

    # Step 2: Screenshot
    ss_path = os.path.join(OUTPUT_DIR, "debug_screenshot.png")
    page.screenshot(path=ss_path)
    print(f"[2] Screenshot saved: {ss_path}")

    # Step 3: Check for dialog
    dialog = page.query_selector('div[role="dialog"]')
    print(f"[3] Dialog found: {dialog is not None}")

    # Step 4: Dump full page HTML structure (just key parts)
    html = page.content()
    html_path = os.path.join(OUTPUT_DIR, "debug_full_page.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[4] Full page HTML saved: {html_path}")

    # Step 5: Find all hrefs that look like profiles
    all_hrefs = re.findall(r'href="/([a-zA-Z0-9._]{1,30})/"', html)
    excluded = {"about", "accounts", "direct", "directory", "explore", "graphql",
                "p", "press", "reel", "reels", "stories", "tv", "followers", "following",
                "login", "signup", "emails", "settings", "nametag", "session"}
    usernames = [u.lower() for u in all_hrefs if u.lower() not in excluded and u.lower() != target]
    unique = list(dict.fromkeys(usernames))
    print(f"[5] Usernames found before scrolling: {len(unique)}")
    for u in unique[:20]:
        print(f"    @{u}")

    # Step 6: Try to find scrollable elements
    print(f"\n[6] Looking for scrollable elements...")
    scroll_info = page.evaluate("""() => {
        const results = [];
        const dialog = document.querySelector('div[role="dialog"]');
        const searchRoot = dialog || document.body;
        const allDivs = searchRoot.querySelectorAll('div');

        for (const div of allDivs) {
            const style = window.getComputedStyle(div);
            const isScrollable = div.scrollHeight > div.clientHeight + 10;
            const hasOverflow = ['auto', 'scroll', 'hidden'].includes(style.overflowY) ||
                               ['auto', 'scroll', 'hidden'].includes(style.overflow);
            if (isScrollable && hasOverflow) {
                results.push({
                    tag: div.tagName,
                    classes: div.className.substring(0, 80),
                    scrollHeight: div.scrollHeight,
                    clientHeight: div.clientHeight,
                    overflowY: style.overflowY,
                    overflow: style.overflow,
                    childCount: div.children.length,
                    role: div.getAttribute('role') || '',
                    style_attr: (div.getAttribute('style') || '').substring(0, 100),
                });
            }
        }
        return results;
    }""")

    if scroll_info:
        print(f"  Found {len(scroll_info)} scrollable elements:")
        for i, info in enumerate(scroll_info):
            print(f"    [{i}] scrollH={info['scrollHeight']} clientH={info['clientHeight']} "
                  f"overflow={info['overflowY']} children={info['childCount']} "
                  f"role='{info['role']}' classes='{info['classes'][:50]}'")
    else:
        print("  NO scrollable elements found!")

    # Step 7: Try scrolling and see if new users appear
    print(f"\n[7] Attempting to scroll...")

    for attempt in range(5):
        # Method 1: Scroll all found scrollable elements
        page.evaluate("""() => {
            const dialog = document.querySelector('div[role="dialog"]');
            const searchRoot = dialog || document.body;
            const allDivs = searchRoot.querySelectorAll('div');

            for (const div of allDivs) {
                const style = window.getComputedStyle(div);
                const isScrollable = div.scrollHeight > div.clientHeight + 10;
                const hasOverflow = ['auto', 'scroll', 'hidden'].includes(style.overflowY) ||
                                   ['auto', 'scroll', 'hidden'].includes(style.overflow);
                if (isScrollable && hasOverflow) {
                    div.scrollTop = div.scrollHeight;
                }
            }
            // Also scroll the page itself
            window.scrollTo(0, document.body.scrollHeight);
        }""")

        time.sleep(2 + random.uniform(0.2, 0.5))

        # Re-extract usernames
        html = page.content()
        all_hrefs = re.findall(r'href="/([a-zA-Z0-9._]{1,30})/"', html)
        usernames = [u.lower() for u in all_hrefs if u.lower() not in excluded and u.lower() != target]
        unique = list(dict.fromkeys(usernames))
        print(f"  Scroll {attempt+1}: {len(unique)} usernames found")

    # Step 8: Also try mouse wheel scroll on dialog
    print(f"\n[8] Trying mouse wheel scroll on dialog center...")
    if dialog:
        box = dialog.bounding_box()
        if box:
            cx = box['x'] + box['width'] / 2
            cy = box['y'] + box['height'] / 2
            for i in range(5):
                page.mouse.wheel(0, 500)  # scroll down 500px
                time.sleep(1.5)
                html = page.content()
                all_hrefs = re.findall(r'href="/([a-zA-Z0-9._]{1,30})/"', html)
                usernames = [u.lower() for u in all_hrefs if u.lower() not in excluded and u.lower() != target]
                unique = list(dict.fromkeys(usernames))
                print(f"  Mouse wheel {i+1}: {len(unique)} usernames")

    # Final screenshot
    ss2_path = os.path.join(OUTPUT_DIR, "debug_screenshot_after_scroll.png")
    page.screenshot(path=ss2_path)
    print(f"\n[9] Screenshot after scroll: {ss2_path}")

    # Final usernames
    print(f"\n[10] Final unique usernames ({len(unique)}):")
    for u in unique[:50]:
        print(f"    @{u}")

    browser.close()
    pw.stop()
    print("\nDone! Check the output/ folder for screenshots and HTML dump.")


if __name__ == "__main__":
    main()
