import os
import smtplib
import time
import logging
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from google import genai 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to write to 'agent.log' and standard output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================= CONFIGURATION =================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright_profile")

# This is where you put the URLs of the products you want to check on
URLS = {
    "https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Wash, 34x34",
    "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Rinse, 34x34"
}

# Initialize the GenAI Client
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

# Change the contents area to match whatever product you are checking on
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
            
            # Extract tokens
            in_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            out_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            
            return {
                "text": response.text,
                "in_tokens": in_tokens,
                "out_tokens": out_tokens
            }
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    logging.warning(f"Rate limited (429). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return {"text": f"Error: Request failed after {max_retries} retries due to rate limiting.", "in_tokens": 0, "out_tokens": 0}
            else:
                return {"text": f"Error: {e}", "in_tokens": 0, "out_tokens": 0}

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
    current_time_str = time.strftime('%m/%d/%y, %I:%M %p').lstrip("0").replace(" 0", " ")
    logging.info(f"\n\n{'='*20} Start task on {current_time_str} {'='*20}")

    full_report = "Old Navy Price Check Report\n" + ("="*30) + "\n"
    total_in_tokens = 0
    total_out_tokens = 0
    
    with sync_playwright() as p:
        logging.info(f"Launching isolated Playwright profile at: {USER_DATA_DIR}")
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # Debug by setting to False
        )
        page = context.new_page()

        for url, title in URLS.items():
            result_data = get_price_via_vision(page, url)
            result_text = result_data["text"]
            
            total_in_tokens += result_data["in_tokens"]
            total_out_tokens += result_data["out_tokens"]
            
            # Put Price, Shipping, and Pickup each on their own line
            formatted_text = result_text.replace(", Shipping:", "\nShipping:").replace(", Pickup:", "\nPickup:")
            
            full_report += f"\nItem: {title}\nURL: {url}\n{formatted_text}\n"
            full_report += "-"*30
            logging.info(f"Result for {title}: {result_text}")
            
        context.close()

    # Calculate Cost for Gemini 2.5 Flash, valid as of March 2026
    # Input: $0.30 per 1M tokens
    # Output: $2.50 per 1M tokens
    input_cost = (total_in_tokens / 1_000_000) * 0.30
    output_cost = (total_out_tokens / 1_000_000) * 2.50
    total_cost = input_cost + output_cost

    analytics_block = f"""
\nSession Analytics:
Total Input Tokens:  {total_in_tokens:,}
Total Output Tokens: {total_out_tokens:,}
Estimated Cost:      ${total_cost:.5f}
"""
    full_report += analytics_block

    logging.info(f"\nFinal Report:\n{full_report}")
    send_email(full_report)

if __name__ == "__main__":
    main()