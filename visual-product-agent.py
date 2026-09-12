import base64
import os
import smtplib
import time
import logging
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from openai import OpenAI
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Add it to the local .env file.")

MODEL_NAME = "gpt-5.6-luna"
REASONING_EFFORT = "high"
INPUT_COST_PER_MILLION_TOKENS = 0.20
CACHED_INPUT_COST_PER_MILLION_TOKENS = 0.02
OUTPUT_COST_PER_MILLION_TOKENS = 1.20

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright_profile")

# This is where you put the URLs of the products you want to check on
URLS = {
    "https://oldnavy.gap.com/browse/product.do?pid=5844620023432&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Wash, 34x34",
    "https://oldnavy.gap.com/browse/product.do?pid=5844470023432&vid=1#pdp-page-content": "Structured Straight Non-Stretch Jeans, Dark Rinse, 34x34"
}

# Initialize the OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

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
    logging.info(f"Analyzing with OpenAI {MODEL_NAME} ({REASONING_EFFORT} reasoning)...")
    with open(screenshot_path, "rb") as f:
        image_bytes = f.read()
    image_data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")

    # Change the prompt text above to match whatever product you are checking on.
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model=MODEL_NAME,
                reasoning={"effort": REASONING_EFFORT},
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Analyze this Old Navy product page screenshot. Extract the price and availability strictly based on the visible text. Do not guess. If information is cut off or not explicitly visible, you must say 'Not Visible'. Return exactly in this format:\nPrice: [value or 'Not Visible']\nShipping: [Available / Unavailable / Not Visible]\nPickup: [Available / Unavailable / Not Visible]"
                            },
                            {
                                "type": "input_image",
                                "image_url": image_data_url,
                                "detail": "high"
                            }
                        ]
                    }
                ]
            )
            
            # Extract tokens
            usage = response.usage
            in_tokens = usage.input_tokens if usage else 0
            input_token_details = getattr(usage, "input_tokens_details", None)
            cached_in_tokens = getattr(input_token_details, "cached_tokens", 0) or 0
            out_tokens = usage.output_tokens if usage else 0
            
            return {
                "text": response.output_text,
                "in_tokens": in_tokens,
                "cached_in_tokens": cached_in_tokens,
                "out_tokens": out_tokens
            }
        except Exception as e:
            if getattr(e, "status_code", None) == 429 or "429" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    logging.warning(f"Rate limited (429). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return {"text": f"Error: Request failed after {max_retries} retries due to rate limiting.", "in_tokens": 0, "cached_in_tokens": 0, "out_tokens": 0}
            else:
                return {"text": f"Error: {e}", "in_tokens": 0, "cached_in_tokens": 0, "out_tokens": 0}

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
    total_cached_in_tokens = 0
    total_out_tokens = 0
    
    with sync_playwright() as p:
        logging.info(f"Launching isolated Playwright profile at: {USER_DATA_DIR}")
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 920}
        )
        page = context.new_page()

        for url, title in URLS.items():
            result_data = get_price_via_vision(page, url)
            result_text = result_data["text"]
            
            total_in_tokens += result_data["in_tokens"]
            total_cached_in_tokens += result_data["cached_in_tokens"]
            total_out_tokens += result_data["out_tokens"]
            
            # Put Price, Shipping, and Pickup each on their own line
            formatted_text = result_text.replace(", Shipping:", "\nShipping:").replace(", Pickup:", "\nPickup:")
            
            full_report += f"\nItem: {title}\nURL: {url}\n{formatted_text}\n"
            full_report += "-"*30
            logging.info(f"Result for {title}: {result_text}")
            
        context.close()

    billable_input_tokens = max(total_in_tokens - total_cached_in_tokens, 0)
    input_cost = (billable_input_tokens / 1_000_000) * INPUT_COST_PER_MILLION_TOKENS
    cached_input_cost = (total_cached_in_tokens / 1_000_000) * CACHED_INPUT_COST_PER_MILLION_TOKENS
    output_cost = (total_out_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION_TOKENS
    total_cost = input_cost + cached_input_cost + output_cost

    analytics_block = f"""
\nSession Analytics:
Total Input Tokens:  {total_in_tokens:,}
Cached Input Tokens: {total_cached_in_tokens:,}
Total Output Tokens: {total_out_tokens:,}
Estimated Luna Cost:  ${total_cost:.5f}
"""
    full_report += analytics_block

    logging.info(f"\nFinal Report:\n{full_report}")
    send_email(full_report)

if __name__ == "__main__":
    main()
