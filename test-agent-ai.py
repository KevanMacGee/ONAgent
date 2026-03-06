import os
import smtplib
import time
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# ================= CONFIGURATION (FILL THESE IN) =================
GEMINI_API_KEY = "AIzaSyDv5Mwj8rxqDSsQbGmy0SRrapB-Ir-JJJo"
SENDER_EMAIL = "fidoalert@gmail.com"
EMAIL_APP_PASSWORD = "wtguczzgiwrajxqb"  # No spaces
RECIPIENT_EMAIL = "blackdogretro@gmail.com"

# The path to your Chrome User Data (Bypasses "Greece Ridge" store issues)
# On Windows, it usually looks like: C:/Users/YourName/AppData/Local/Google/Chrome/User Data
USER_DATA_DIR = r"C:\Users\user\AppData\Local\Google\Chrome\User Data"

URLS = [
    "https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content",
    "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content"
]
# ================================================================

genai.configure(api_key="AIzaSyDv5Mwj8rxqDSsQbGmy0SRrapB-Ir-JJJo")
model = genai.GenerativeModel('gemini-1.5-flash')

def get_price_via_vision(page, url):
    page.goto(url, wait_until="networkidle")
    time.sleep(5) # Give the price/size picker a moment to settle
    
    screenshot_path = "temp_price_shot.png"
    page.screenshot(path=screenshot_path, full_page=False)
    
    # Send to Gemini Vision
    img = genai.upload_file(path=screenshot_path)
    prompt = "Look at this Old Navy product page. What is the current price and is size 34W x 34L in stock? Return only: Price: [value], Stock: [In Stock/Out of Stock]"
    
    response = model.generate_content([img, prompt])
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
    
    # Launch Playwright using your REAL browser profile
    with sync_playwright() as p:
        # Note: Chrome must be CLOSED for this to work
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True, # Change to False if you want to watch it work
            channel="chrome"
        )
        page = context.new_page()

        for url in URLS:
            print(f"Checking {url}...")
            result = get_price_via_vision(page, url)
            full_report += f"\nURL: {url}\n{result}\n"
            full_report += "-"*30
            
        context.close()

    print(full_report)
    send_email(full_report)

if __name__ == "__main__":
    main()