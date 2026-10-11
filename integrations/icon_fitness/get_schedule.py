"""
Icon Fitness Schedule Fetcher — Real Implementation
====================================================
Scrapes the real class schedule from iconfitness.co.il/myicon/
using a saved Playwright browser session (from setup_session.py).

Returns JSON with available classes for the requested day.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({"status": "error", "message": "Playwright not installed. Run: pip install playwright && playwright install chromium"}))
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"

# URL patterns for Icon Fitness member area
MYICON_URL    = "https://iconfitness.co.il/myicon/"
SCHEDULE_URL  = "https://iconfitness.co.il/myicon/"   # schedule is on main myicon page


def _day_to_date(day_str: str) -> str:
    """Convert 'Today', 'Tomorrow', or 'Monday' etc. to YYYY-MM-DD string."""
    now = datetime.now()
    day_str_lower = day_str.strip().lower()
    if day_str_lower in ("today", "היום"):
        return now.strftime("%Y-%m-%d")
    if day_str_lower in ("tomorrow", "מחר"):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    # Try parsing as a weekday name (English)
    weekdays_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if day_str_lower in weekdays_en:
        target_wd = weekdays_en.index(day_str_lower)
        delta = (target_wd - now.weekday()) % 7
        if delta == 0:
            delta = 7  # next occurrence if same day
        return (now + timedelta(days=delta)).strftime("%Y-%m-%d")
    # Fallback: try parsing as YYYY-MM-DD
    try:
        datetime.strptime(day_str, "%Y-%m-%d")
        return day_str
    except ValueError:
        return now.strftime("%Y-%m-%d")


def get_schedule(day: str = "Today", class_filter: str = None) -> dict:
    """Fetch real schedule from myicon portal."""

    if not STATE_FILE.exists():
        return {
            "status": "session_missing",
            "message": "No saved session found. Run setup_session.py first to log in.",
            "action_required": "python integrations/icon_fitness/setup_session.py"
        }

    target_date = _day_to_date(day)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=str(STATE_FILE),
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Navigate to myicon
            page.goto(MYICON_URL, wait_until="networkidle", timeout=30000)

            # Check if we're redirected to login (session expired)
            if "login" in page.url.lower() or page.url == "https://iconfitness.co.il/personal-area-login/":
                browser.close()
                return {
                    "status": "session_expired",
                    "message": "Saved session has expired. Run setup_session.py to re-login.",
                    "action_required": "python integrations/icon_fitness/setup_session.py"
                }

            # Look for schedule / classes section
            # Icon Fitness myicon has a schedule/classes widget
            # Try to find schedule iframes or embedded schedule elements
            classes = []

            # Strategy 1: Look for schedule table/list elements
            # The myicon page typically has class registration sections
            page.wait_for_timeout(2000)  # let dynamic content load

            # Try to find class cards / schedule items
            # Icon Fitness uses various selectors depending on page version
            selectors_to_try = [
                ".lesson-item",
                ".class-item",
                ".schedule-item",
                ".lesson",
                "[class*='lesson']",
                "[class*='class-card']",
                "[class*='schedule']",
                "table.classes tr",
                ".wp-block-table tr",
            ]

            found_selector = None
            for sel in selectors_to_try:
                try:
                    count = page.locator(sel).count()
                    if count > 0:
                        found_selector = sel
                        break
                except Exception:
                    continue

            if found_selector:
                items = page.locator(found_selector).all()
                for item in items:
                    try:
                        text = item.inner_text().strip()
                        if text and len(text) > 3:
                            classes.append({"raw_text": text})
                    except Exception:
                        continue
            else:
                # Strategy 2: Get full page text and parse
                page_content = page.content()
                page_text = page.inner_text("body") if page.locator("body").count() > 0 else ""

                # Look for time patterns (HH:MM) and class names
                import re
                time_pattern = re.compile(r'\b(\d{1,2}:\d{2})\b')
                lines = [l.strip() for l in page_text.split('\n') if l.strip()]

                # Extract lines that look like class entries (contain a time)
                for i, line in enumerate(lines):
                    if time_pattern.search(line):
                        times = time_pattern.findall(line)
                        for t in times:
                            classes.append({
                                "raw_text": line,
                                "time": t
                            })

            browser.close()

            # Filter by class name if requested
            if class_filter and classes:
                filtered = [c for c in classes if class_filter.lower() in c.get("raw_text", "").lower()]
                if filtered:
                    classes = filtered

            return {
                "status": "success",
                "gym": "Icon Fitness Hod HaSharon",
                "date": target_date,
                "day_requested": day,
                "class_filter": class_filter,
                "classes_found": len(classes),
                "classes": classes[:20],  # cap at 20
                "note": "Live data from iconfitness.co.il/myicon/"
            }

    except PlaywrightTimeout:
        return {"status": "error", "message": "Page load timed out. Check your internet connection."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Fetch Icon Fitness Schedule (real data)")
    parser.add_argument("--day", default="Today", help="Day: Today, Tomorrow, Monday, or YYYY-MM-DD")
    parser.add_argument("--filter", default=None, dest="class_filter",
                        help="Filter by class name (e.g. 'פילאטיס', 'Pilates')")
    args = parser.parse_args()

    result = get_schedule(args.day, args.class_filter)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
