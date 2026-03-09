import os
import smtplib
import time
import logging
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from google import genai  # The modern 2026 library

# Configure logging to write to 'agent.log' and standard output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================= CONFIGURATION (FILL THESE IN) =================
GEMINI_API_KEY = "AIzaSyDv5Mwj8rxqDSsQbGmy0SRrapB-Ir-JJJo" 
SENDER_EMAIL = "fidoalert@gmail.com"
EMAIL_APP_PASSWORD = "wtguczzgiwrajxqb" 
RECIPIENT_EMAIL = "blackdogretro@gmail.com"

# Using your Gateway path - Ensure 'User' is correct
USER_DATA_DIR = r"C:\Users\User\AppData\Local\Google\Chrome\User Data"
PROFILE_NAME = "Default" 

URLS = {
    "https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Wash, 34x34",
    "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Rinse, 34x34"
}
# ================================================================

# Initialize the 2026 GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

def get_price_via_vision(page, url):
    logging.info(f"Navigating to {url}...")
    try:
        # We only wait for 'commit' because we are using our eyes, not their code
        page.goto(url, wait_until="commit", timeout=10000)
    except Exception as e:
        logging.warning(f"Navigation info: {e} (Moving to screenshot anyway...)")

    logging.info("Waiting 7 seconds for visual settle...")
    time.sleep(7) 
    
    screenshot_path = "temp_price_shot.png"
    page.screenshot(path=screenshot_path, full_page=False)
    logging.info("Analyzing with Gemini 2.5 Flash...")
    with open(screenshot_path, "rb") as f:
        image_bytes = f.read()

    # The 2026-stable call structure
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Look at this Old Navy product page. What is the current price? Is it available for shipping? Is it available for in-store pickup? Return only: Price: [value], Shipping: [Available/Unavailable], Pickup: [Available/Unavailable]",
                    {"inline_data": {"data": image_bytes, "mime_type": "image/png"}}
                ]
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    logging.warning(f"Rate limited (429). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Error: Request failed after {max_retries} retries due to rate limiting."
            else:
                return f"Error: {e}"

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
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def main():
    full_report = "Old Navy Price Check Report\n" + ("="*30) + "\n"
    
    with sync_playwright() as p:
        logging.info(f"Launching Chrome profile: {PROFILE_NAME}...")
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # Debug by setting to False
            args=[f"--profile-directory={PROFILE_NAME}"]
        )
        page = context.new_page()

        for url, title in URLS.items():
            result = get_price_via_vision(page, url)
            full_report += f"\nItem: {title}\nURL: {url}\n{result}\n"
            full_report += "-"*30
            logging.info(f"Result for {title}: {result}")
            
        context.close()

    logging.info(f"\nFinal Report:\n{full_report}")
    send_email(full_report)

if __name__ == "__main__":
    main()