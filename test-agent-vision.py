from playwright.sync_api import sync_playwright
import time
import os

URLS = [
    {"name": "Dark_Rinse", "url": "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content"},
    {"name": "Dark_Wash", "url": "https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content"}
]

USER_DATA_DIR = os.path.join(os.getcwd(), "on_profile")

def capture_for_ai():
    with sync_playwright() as p:
        print("--- Old Navy Vision: Capturing State ---")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 1200} # Taller to see the stock boxes
        )
        page = context.new_page()

        for item in URLS:
            print(f"Capturing {item['name']}...")
            try:
                page.goto(item['url'], wait_until="load")
                time.sleep(7) # Give it plenty of time to 'settle'
                
                # Take a screenshot of the top half of the page where price/stock are
                page.screenshot(path=f"{item['name']}_view.png")
                print(f"  Saved: {item['name']}_view.png")
                
            except Exception as e:
                print(f"  Failed to capture {item['name']}: {e}")

        context.close()

if __name__ == "__main__":
    capture_for_ai()