"""
Icon Fitness Auto-Registration Engine — Real Implementation
============================================================
Uses Playwright + saved session to navigate myicon portal
and register for a Pilates (or other) class.

Triggered by Leo via: invoke_leo.py --register
Requires: setup_session.py to have been run first.
"""

import json
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({"status": "error", "message": "Playwright not installed. Run: pip install playwright && playwright install chromium"}))
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"

MYICON_URL = "https://iconfitness.co.il/myicon/"


def _day_to_date(day_str: str) -> str:
    now = datetime.now()
    day_str_lower = day_str.strip().lower()
    if day_str_lower in ("today", "היום"):
        return now.strftime("%Y-%m-%d")
    if day_str_lower in ("tomorrow", "מחר"):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    weekdays_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if day_str_lower in weekdays_en:
        target_wd = weekdays_en.index(day_str_lower)
        delta = (target_wd - now.weekday()) % 7
        if delta == 0:
            delta = 7
        return (now + timedelta(days=delta)).strftime("%Y-%m-%d")
    try:
        datetime.strptime(day_str, "%Y-%m-%d")
        return day_str
    except ValueError:
        return now.strftime("%Y-%m-%d")


def register_for_class(class_name: str, day: str, time_str: str, dry_run: bool = False) -> dict:
    """
    Navigate myicon portal and register for the specified class.

    Args:
        class_name: e.g. "פילאטיס", "Pilates", "Body Pump"
        day: "Today", "Tomorrow", "Monday", or "YYYY-MM-DD"
        time_str: "HH:MM" e.g. "18:00"
        dry_run: If True, find the class but don't click register (for testing)
    """

    if not STATE_FILE.exists():
        return {
            "status": "session_missing",
            "message": "No saved session. Run setup_session.py first.",
            "action_required": "python integrations/icon_fitness/setup_session.py"
        }

    target_date = _day_to_date(day)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # headed so you can see what happens
            context = browser.new_context(
                storage_state=str(STATE_FILE),
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # ── Step 1: Navigate to myicon ──────────────────────────────────
            page.goto(MYICON_URL, wait_until="networkidle", timeout=30000)

            # Check if session is still valid
            if "login" in page.url.lower() or "personal-area-login" in page.url:
                browser.close()
                return {
                    "status": "session_expired",
                    "message": "Session expired. Please run setup_session.py to re-login.",
                    "action_required": "python integrations/icon_fitness/setup_session.py"
                }

            page.wait_for_timeout(2000)

            # ── Step 2: Find schedule section & navigate to correct date ────
            # Icon Fitness myicon has a schedule widget/section
            # Try clicking on schedule / שיעורים tab if present
            schedule_selectors = [
                "a:has-text('שיעורים')",
                "a:has-text('לוח שיעורים')",
                "button:has-text('שיעורים')",
                "[href*='schedule']",
                "[href*='lessons']",
                ".schedule-tab",
                "#schedule",
            ]

            for sel in schedule_selectors:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.click()
                        page.wait_for_timeout(1500)
                        break
                except Exception:
                    continue

            # ── Step 3: Navigate to the target date ─────────────────────────
            # If there's a date picker / forward button, click to reach target_date
            today_str = datetime.now().strftime("%Y-%m-%d")
            days_ahead = (datetime.strptime(target_date, "%Y-%m-%d") - datetime.now()).days

            if days_ahead > 0:
                next_day_selectors = [
                    "button:has-text('>')",
                    "button:has-text('הבא')",
                    "button:has-text('הבאה')",
                    ".next-day",
                    "[aria-label='next']",
                    "[aria-label='הבא']",
                    ".swiper-button-next",
                ]
                for _ in range(min(days_ahead, 7)):
                    for sel in next_day_selectors:
                        try:
                            btn = page.locator(sel).first
                            if btn.count() > 0 and btn.is_visible():
                                btn.click()
                                page.wait_for_timeout(800)
                                break
                        except Exception:
                            continue

            page.wait_for_timeout(1500)

            # ── Step 4: Find the target class ───────────────────────────────
            # Look for class entries matching class_name and time_str
            class_name_lower = class_name.lower()
            time_clean = time_str.strip()

            # Collect all text nodes that mention the class
            page_text = page.inner_text("body")
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]

            matching_lines = []
            for line in lines:
                if class_name_lower in line.lower() and time_clean in line:
                    matching_lines.append(line)

            # Try to find and click a register button near the matching class
            # Common button text patterns on Icon Fitness
            register_btn_texts = [
                "הרשמה",
                "הרשם",
                "רשום אותי",
                "Book",
                "Register",
                "להרשמה",
            ]

            registered = False
            register_btn_clicked = None

            # Strategy A: Find class element by text, then find nearby register button
            class_locators_to_try = [
                f"text='{class_name}'",
                f"*:has-text('{class_name}')",
            ]

            for class_sel in class_locators_to_try:
                try:
                    class_els = page.locator(class_sel).all()
                    for class_el in class_els:
                        try:
                            el_text = class_el.inner_text()
                            if time_clean in el_text:
                                # Found the right class entry — look for register button within parent
                                parent = class_el.locator("xpath=ancestor::div[contains(@class,'lesson') or contains(@class,'class') or contains(@class,'item')][1]")
                                if parent.count() == 0:
                                    parent = class_el.locator("xpath=..")

                                for btn_text in register_btn_texts:
                                    try:
                                        btn = parent.locator(f"button:has-text('{btn_text}'), a:has-text('{btn_text}')").first
                                        if btn.count() > 0 and btn.is_visible():
                                            if not dry_run:
                                                btn.click()
                                                page.wait_for_timeout(2000)
                                            register_btn_clicked = btn_text
                                            registered = True
                                            break
                                    except Exception:
                                        continue
                                if registered:
                                    break
                        except Exception:
                            continue
                    if registered:
                        break
                except Exception:
                    continue

            # Strategy B: Broader search — find any register button near the class name
            if not registered:
                for btn_text in register_btn_texts:
                    try:
                        btns = page.locator(f"button:has-text('{btn_text}'), a:has-text('{btn_text}')").all()
                        for btn in btns:
                            try:
                                # Check surrounding context for class name and time
                                parent_text = ""
                                for ancestor_sel in ["xpath=ancestor::div[1]", "xpath=ancestor::div[2]", "xpath=ancestor::tr[1]"]:
                                    try:
                                        ancestor = btn.locator(ancestor_sel)
                                        if ancestor.count() > 0:
                                            parent_text = ancestor.inner_text()
                                            break
                                    except Exception:
                                        continue

                                if class_name_lower in parent_text.lower() and time_clean in parent_text:
                                    if not dry_run:
                                        btn.click()
                                        page.wait_for_timeout(2000)
                                    register_btn_clicked = btn_text
                                    registered = True
                                    break
                            except Exception:
                                continue
                        if registered:
                            break
                    except Exception:
                        continue

            # ── Step 5: Confirm registration dialog if present ──────────────
            if registered and not dry_run:
                confirm_selectors = [
                    "button:has-text('אישור')",
                    "button:has-text('כן')",
                    "button:has-text('Confirm')",
                    "button:has-text('OK')",
                    ".confirm-btn",
                ]
                for sel in confirm_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.count() > 0 and btn.is_visible(timeout=3000):
                            btn.click()
                            page.wait_for_timeout(1500)
                            break
                    except Exception:
                        continue

            # ── Step 6: Capture final page state ────────────────────────────
            final_url = page.url
            final_title = page.title()

            # Take screenshot for debugging
            screenshot_path = ROOT / f"last_registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(screenshot_path))

            browser.close()

            if registered:
                return {
                    "status": "success" if not dry_run else "dry_run_success",
                    "message": f"{'Registered' if not dry_run else '[DRY RUN] Found class —'} {class_name} on {target_date} at {time_str}",
                    "gym": "Icon Fitness Hod HaSharon",
                    "class_name": class_name,
                    "date": target_date,
                    "time": time_str,
                    "register_button_found": register_btn_clicked,
                    "screenshot": str(screenshot_path),
                    "final_url": final_url,
                }
            else:
                return {
                    "status": "class_not_found",
                    "message": f"Could not find '{class_name}' at {time_str} on {target_date}. The class may be full, not open for registration yet, or the page structure changed.",
                    "matching_text_found": matching_lines,
                    "gym": "Icon Fitness Hod HaSharon",
                    "screenshot": str(screenshot_path),
                    "suggestion": "Run --schedule to see available classes, then retry with exact class name and time.",
                }

    except PlaywrightTimeout:
        return {"status": "error", "message": "Timed out loading Icon Fitness. Check internet connection."}
    except Exception as e:
        return {"status": "error", "message": f"{type(e).__name__}: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="Icon Fitness Auto-Registration (Leo)")
    parser.add_argument("--class-name", required=True, help="Class name, e.g. 'פילאטיס' or 'Pilates'")
    parser.add_argument("--day", default="Today", help="Day: Today, Tomorrow, Monday, or YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="Class time, e.g. 18:00")
    parser.add_argument("--dry-run", action="store_true", help="Find class but don't actually register")
    args = parser.parse_args()

    result = register_for_class(args.class_name, args.day, args.time, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
