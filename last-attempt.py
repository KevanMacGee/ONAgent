import os
import smtplib
import time
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from google import genai  # The modern 2026 library

# ================= CONFIGURATION (FILL THESE IN) =================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 
SENDER_EMAIL = "fidoalert@gmail.com"
EMAIL_APP_PASSWORD = "your-16-digit-app-password" 
RECIPIENT_EMAIL = "your-email@gmail.com"

# Using your Gateway path - Ensure 'User' is correct
USER_DATA_DIR = r"C:\Users\User\AppData\Local\Google\Chrome\User Data"
PROFILE_NAME = "Default" 

URLS = [
    "https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content",
    "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content"
]
# ================================================================

# Initialize the 2026 GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

def get_price_via_vision(page, url):
    print(f"Navigating to {url}...")
    try:
        # We only wait for 'commit' because we are using our eyes, not their code
        page.goto(url, wait_until="commit", timeout=10000)
    except Exception as e:
        print(f"Navigation info: {e} (Moving to screenshot anyway...)")

    print("Waiting 7 seconds for visual settle...")
    time.sleep(7) 
    
    screenshot_path = "temp_price_shot.png"
    page.screenshot(path=screenshot_path, full_page=False)
    
    print("Analyzing with Gemini 2.0 Flash...")
    with open(screenshot_path, "rb") as f:
        image_bytes = f.read()

    # The 2026-stable call structure
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Look at this Old Navy product page. What is the current price and is size 34W x 34L in stock? Return only: Price: [value], Stock: [In Stock/Out of Stock]",
            {"inline_data": {"data": image_bytes, "mime_type": "image/png"}}
        ]
    )
    return response.text

def send_email(report_body):
    msg = EmailMessage()
    msg.set_content(report_body)
    msg['Subject'] = f"Old Navy Agent Run - {time.strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    full_report = "Old Navy Price Check Report\n" + ("="*30) + "\n"
    
    with sync_playwright() as p:
        print(f"Launching Chrome profile: {PROFILE_NAME}...")
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
            channel="chrome",
            args=[f"--profile-directory={PROFILE_NAME}"]
        )
        page = context.new_page()

        for url in URLS:
            result = get_price_via_vision(page, url)
            full_report += f"\nURL: {url}\n{result}\n"
            full_report += "-"*30
            print(f"Result: {result}")
            
        context.close()

    print("\nFinal Report:\n", full_report)
    send_email(full_report)

if __name__ == "__main__":
    main()