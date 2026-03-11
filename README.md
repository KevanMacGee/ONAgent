# Visual Web Scraper Agent (Playwright + Gemini AI)

Sometimes you write an agent to solve important business needs, sometimes you write an agent to buy cheap jeans to wear to the muddy, messy dog park.

This is a lightweight, automated Python agent that navigates to e-commerce product pages (like Old Navy), visually captures the page, and uses the Gemini 2.5 Flash multimodal AI to extract price and availability information. It then compiles an email report and sends it to you.

## Why this approach?

Instead of relying on fragile HTML parsing that breaks whenever a website updates its design, this script uses **Playwright** to open a real browser window and **Gemini Vision** to "look" at a screenshot of the page. It's resilient, easy to adapt to any website, and incredibly cheap to run.

## Features

- Launches a persistent Chrome profile (preserves cookies, sessions, and helps avoid bot detection).
- Takes visual screenshots of target web pages.
- Uses Google's Gemini 2.5 Flash model to extract precise information (Price, Shipping status, Pickup availability).
- Automatically calculates API costs per run.
- Sends a formatted email report with the extracted data.

## Prerequisites

- Python 3.8+
- A Google Gemini API Key
- A Gmail account with an App Password generated (for sending emails)
- Google Chrome installed

## Setup Instructions

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install playwright google-genai python-dotenv
playwright install chromium
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory of the project and add your credentials:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
SENDER_EMAIL=your_sending_gmail@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=where_to_send_report@example.com

# Chrome Profile Configuration
# On Windows, this is typically: C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data
CHROME_USER_DATA_DIR=C:\path\to\your\chrome\User Data
CHROME_PROFILE_NAME=Profile 1 # Or "Default", "Profile 2", etc.
```

_Note: Using a persistent Chrome profile allows the script to mimic your actual browser. Make sure all instances of Chrome using that specific profile are closed before running the script, otherwise Playwright will fail to launch it._

### 3. Customize the Target URLs

Open the `visual-product-agent.py` file and modify the `URLS` dictionary. The key should be the target URL, and the value should be the product name or title you want to appear in the email report.

```python
URLS = {
    "https://example.com/product/123": "My Favorite Product",
    "https://example.com/product/456": "Another Product"
}
```

### 4. Customize the Prompt (Optional)

If you are scraping something other than Old Navy, you'll need to update the prompt sent to Gemini. Find this section in `visual-product-agent.py`:

```python
contents=[
    "Look at this Old Navy product page. What is the current price? Is it available for shipping? Is it available for in-store pickup? Return only: Price: [value], Shipping: [Available/Unavailable], Pickup: [Available/Unavailable]",
    {"inline_data": {"data": image_bytes, "mime_type": "image/png"}}
]
```

Adjust the text instruction to ask Gemini for whatever information is relevant to the page you are scraping.

## Running the Script

Execute the script manually to test it:

```bash
python visual-product-agent.py
```

### Background Execution & Scheduling

By default, `headless=False` is set in the Playwright launch options for easy debugging. If you plan to schedule this script via **Windows Task Scheduler** or a **Cron job**, you may want to change it to `headless=True` so a visible browser window doesn't pop up and interrupt your work.

```python
context = p.chromium.launch_persistent_context(
    USER_DATA_DIR,
    headless=True,  # Change to True for automated background running
    args=[f"--profile-directory={PROFILE_NAME}"]
)
```

## Logs and Debugging

- The script preserves the last captured screenshot as `temp_price_shot.png` in the directory. This is useful for debugging if the script encounters a navigation error or if Gemini returns unexpected results.
- All actions, errors, and rate limit retries are logged to `agent.log`.

## Cost

Using Gemini 2.5 Flash is highly cost-effective and includes a generous free tier. The script automatically calculates and appends the estimated cost (typically fractions of a penny) to the bottom of the email report for complete transparency.
