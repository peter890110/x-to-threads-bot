"""Capture the real X embed for a post, including quoted posts and original UI."""
from pathlib import Path
from playwright.sync_api import sync_playwright


def capture_x_post(tweet_id):
    output = Path("generated_cards") / f"{tweet_id}.png"
    output.parent.mkdir(exist_ok=True)
    url = f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}&theme=light"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 1600}, device_scale_factor=2)
            page.goto(url, wait_until="networkidle", timeout=45000)
            tweet = page.locator("article").first
            tweet.wait_for(state="visible", timeout=20000)
            tweet.screenshot(path=str(output))
            browser.close()
        return output
    except Exception as error:
        print(f"X 貼文截圖失敗：{error}")
        return None
