import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"
ICON_URL = "https://www.iconfitness.co.il/personal-area-login/"

def setup_session():
    print("Starting browser for manual login...")
    with sync_playwright() as p:
        # Launch headed browser so the user can interact with it
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to {ICON_URL}")
        page.goto(ICON_URL)

        print("\n" + "="*60)
        print("ACTION REQUIRED:")
        print("1. Select your club (Hod Hasharon).")
        print("2. Enter your phone number and request the SMS code.")
        print("3. Enter the SMS code and log in.")
        print("4. Once you see your personal dashboard, return to this terminal.")
        print("="*60 + "\n")

        input("Press ENTER here *AFTER* you have successfully logged in...")

        # Save the session state (cookies, local storage)
        context.storage_state(path=STATE_FILE)
        print(f"\n[SUCCESS] Session saved to {STATE_FILE}!")
        print("Leo can now use this session to register you automatically.")

        browser.close()

if __name__ == "__main__":
    setup_session()
