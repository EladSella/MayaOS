from playwright.sync_api import sync_playwright
import os

def check():
    path = "file:///" + os.path.abspath("test_embed.html").replace("\\", "/")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(path)
        page.wait_for_timeout(3000)
        page.screenshot(path="embed_test.png")
        print("Done")
        browser.close()

if __name__ == '__main__':
    check()
