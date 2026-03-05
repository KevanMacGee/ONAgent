from playwright.sync_api import sync_playwright
import time
import os

URLS = [
    {"name": "Dark Rinse", "url": "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content"},
    {"name": "Dark Wash", "url": "https://oldnavy.gap.com/browse/product.do?pid=5844470220000"} # Updated with a likely wash ID
]

USER_DATA_DIR = os.path.join(os.getcwd(), "on_profile")

def check_jeans():
    with sync_playwright() as p:
        print(f"--- Old Navy Agent: Deep Cover Mode ---")
        
        # This setup makes the bot look exactly like a real user
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        for item in URLS:
            print(f"\n[{item['name']}] Checking...")
            try:
                page.goto(item['url'], wait_until="domcontentloaded")
                
                # 1. Wait specifically for price data to arrive
                print("  Waiting for price to load...")
                price_selector = ".pdp-pricing__selected-price"
                page.wait_for_selector(f"{price_selector}:has-text('$')", timeout=15000)
                
                # 2. Extract Data
                price = page.locator(price_selector).first.inner_text()
                
                # We'll use a broader search for the fulfillment boxes
                full_text = page.content()
                
                shipping = "In Stock" if "In stock for shipping" in full_text else "Out of Stock"
                pickup = "In Stock" if "In stock for pickup" in full_text else "Out of Stock"
                atb_visible = page.locator('button:has-text("Add to Bag")').is_visible()

                print(f"  Result: {price}")
                print(f"  Fulfillment: Ship({shipping}) | Pickup({pickup})")
                print(f"  ATB Button: {'✅' if atb_visible else '❌'}")

            except Exception as e:
                print(f"  Timeout/Error: Price didn't load in time. (Check your URL/Size selection)")

        print("\nAll tasks finished.")
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    check_jeans()