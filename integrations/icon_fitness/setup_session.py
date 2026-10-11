"""
Icon Fitness Session Setup — Diagnostic Version
================================================
This version captures the actual URL and session state after login,
to figure out exactly where the authenticated session lives.
"""

import sys
import json
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"

# Start at the login page — let the user navigate anywhere they want
LOGIN_URL = "https://www.iconfitness.co.il/personal-area-login/"


def setup_session():
    print("Starting browser for manual login...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Opening: {LOGIN_URL}")
        page.goto(LOGIN_URL)

        print()
        print("=" * 60)
        print("ACTION REQUIRED:")
        print("1. Select your club (Hod Hasharon).")
        print("2. Enter your phone number + SMS code.")
        print("3. Log in and wait until you see your dashboard.")
        print("4. IMPORTANT: After you see your dashboard,")
        print("   also click on 'שיעורים' or the class schedule")
        print("   section if there is one, then come back here.")
        print("=" * 60)
        print()

        input("Press ENTER here *AFTER* you are logged in and can see your dashboard...")

        # Capture current state immediately
        current_url = page.url
        current_title = page.title()
        print(f"\nCurrent URL: {current_url}")
        print(f"Current title: {current_title}")

        # Save state — all cookies across all domains visited
        context.storage_state(path=str(STATE_FILE))

        # Print what was captured
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)

        cookies = saved.get('cookies', [])
        origins = saved.get('origins', [])

        print(f"\n--- CAPTURED SESSION ---")
        print(f"Cookies: {len(cookies)}")
        for c in cookies:
            print(f"  [{c.get('domain')}] {c.get('name')} = {str(c.get('value',''))[:50]}")

        print(f"\nOrigins with localStorage: {len(origins)}")
        for o in origins:
            ls_items = o.get('localStorage', [])
            print(f"  {o.get('origin')}: {len(ls_items)} items")
            for item in ls_items:
                name = item.get('name', '')
                val = str(item.get('value', ''))[:100]
                print(f"    {name} = {val}")

        print(f"\n[SAVED] Session stored at: {STATE_FILE}")

        if "login" in current_url.lower():
            print("\n⚠️  Still on login page — login may not have completed.")
        else:
            print(f"\n✅ Authenticated! URL: {current_url}")

        browser.close()


if __name__ == "__main__":
    setup_session()
