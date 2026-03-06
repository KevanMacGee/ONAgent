from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\User\AppData\Local\Google\Chrome\User Data"
PROFILE_NAME = "Default" 

def test_launch():
    print(f"Testing Profile Launch with {USER_DATA_DIR} Profile: {PROFILE_NAME}")
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                headless=False,
                args=[f"--profile-directory={PROFILE_NAME}"]
            )
            print("Successfully launched!")
            page = context.new_page()
            page.goto("https://google.com")
            print("Successfully navigated!")
            context.close()
            print("Closed successfully.")
        except Exception as e:
            print(f"Failed to launch: {e}")

if __name__ == "__main__":
    test_launch()
