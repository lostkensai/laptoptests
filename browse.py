from playwright.sync_api import sync_playwright
import time

# 🔗 List of sites (keep this fixed across all tests)
URLS = [
    "https://www.straitstimes.com",
    "https://www.channelnewsasia.com",
    "https://www.bbc.com",
    "https://www.reddit.com",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://www.amazon.com",
    "https://www.youtube.com"
]

# ⏱️ Time per page (seconds)
PAGE_DURATION = 30

# 🖱️ Scroll settings
SCROLL_STEP = 300
SCROLL_DELAY = 1  # seconds


def browse(page):
    for url in URLS:
        print(f"Visiting {url}")
        page.goto(url, timeout=60000)

        start_time = time.time()

        while time.time() - start_time < PAGE_DURATION:
            # Scroll down
            page.mouse.wheel(0, SCROLL_STEP)
            time.sleep(SCROLL_DELAY)

        time.sleep(2)  # small pause before next page


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-notifications",
                "--disable-infobars"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )

        page = context.new_page()

        # 🔁 Loop forever (until battery dies)
        while True:
            browse(page)


if __name__ == "__main__":
    run()