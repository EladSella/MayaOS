from playwright.sync_api import sync_playwright

vids = ['inpok4MKVLM', 'ssss7V1_eyA', 'dEzbdLn2bJc', 'z6X5oEIg6Ak', 'O-6f5wQXSu8', 'krBvzDlL0mM']

def check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-web-security'])
        page = browser.new_page()
        valid = []
        for vid in vids:
            try:
                page.goto(f"https://www.youtube.com/embed/{vid}?rel=0")
                page.wait_for_timeout(2000)
                text = page.locator("body").inner_text()
                if "unavailable" not in text.lower() and "error" not in text.lower() and "private" not in text.lower():
                    valid.append(vid)
                    print(f"{vid} is VALID")
                else:
                    print(f"{vid} is BROKEN. Text: {text[:50]}")
            except Exception as e:
                print(f"{vid} failed: {e}")
        print("ALL VALID:", valid)
        browser.close()

if __name__ == '__main__':
    check()
