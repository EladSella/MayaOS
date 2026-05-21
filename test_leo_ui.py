import sys
from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("http://localhost:8000/leo.html")
        
        # Wait for schedule API to finish
        try:
            page.wait_for_selector(".pilates-place", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        
        container_text = page.locator("#pilates-container").inner_text()
        # print(f"Pilates Container Content:\n{container_text}")
        
        screenshot_path = "C:\\Users\\Elad\\.gemini\\antigravity\\brain\\80f37fe6-6896-4323-97e9-a26bc9ae5e93\\leo_ui_test_final.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print("Screenshot saved!")
        browser.close()

if __name__ == "__main__":
    verify()
