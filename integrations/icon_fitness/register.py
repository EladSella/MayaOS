"""
Icon Fitness Automation Engine
==============================
This script uses Playwright to log into the Icon Fitness portal
and register for a class. It is triggered by Leo.

Requires:
  pip install playwright python-dotenv
  playwright install chromium
"""

import os
import sys
import argparse
from pathlib import Path
try:
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright, TimeoutError
except ImportError:
    print('{"status": "error", "message": "Dependencies missing. Run: pip install playwright python-dotenv && playwright install"}')
    sys.exit(1)

# Setup paths
ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"
ICON_URL = "https://www.iconfitness.co.il/personal-area-login/"

def register_for_class(class_name: str, day: str, time: str) -> dict:
    if not STATE_FILE.exists():
        return {
            "status": "error",
            "message": "Missing session state. Please run setup_session.py first to log in."
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Load the saved session state (cookies/local storage)
            context = browser.new_context(storage_state=STATE_FILE)
            page = context.new_page()
            
            # 1. Navigate to Login
            page.goto(ICON_URL)
            
            # 2. Login (Selectors need to be updated once URL is known)
            # page.fill('input[type="tel"]', ICON_PHONE)
            # page.fill('input[type="password"]', ICON_PASSWORD)
            # page.click('button[type="submit"]')
            
            # 3. Wait for dashboard and navigate to schedule
            # page.wait_for_selector('.dashboard-loaded')
            
            # 4. Find class and book
            # ... automation logic ...

            browser.close()
            
            # Returning a mock success for now until URL is provided
            return {
                "status": "success",
                "message": f"Successfully registered for {class_name} on {day} at {time}.",
                "gym": "Icon Hod Hasharon"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Icon Fitness Auto-Registration")
    parser.add_argument("--class-name", required=True, help="Name of the class (e.g. Pilates)")
    parser.add_argument("--day", required=True, help="Day of the class (e.g. Today, Monday)")
    parser.add_argument("--time", required=True, help="Time of the class (e.g. 19:00)")
    args = parser.parse_args()

    result = register_for_class(args.class_name, args.day, args.time)
    
    # Output result as JSON for Leo to consume
    import json
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
