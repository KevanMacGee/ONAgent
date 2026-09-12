# Visual Web Scraper Agent (Playwright + OpenAI)

**Sometimes you write an agent to solve important business needs, sometimes you write an agent to buy cheap jeans to wear to the muddy dog park.** 

Click [here](#setup-start) if you want to skip the wordy bits and get right to the setup.

Old Navy jeans are normally about $40 - $50 a pair but they go on sale a few times a year for about $15 - 20. I'm rough on my jeans and do a lot of hiking with my dog and have to replace them from time to time. This tool tells me the price and availability of those jeans a few times a week so I can snap them up if I am in need. 

- This is a lightweight, automated agent that uses Python to navigates to (in my example) Old Navy pages for the jeans, and takes a screenshot of the page. 
- It then sends the screenshot to the OpenAI Responses API.
- GPT-5.6 Luna, using high reasoning, looks at the image to find the current price and whether the item is available for shipping and in-store pickup.
- It then emails me that info.
- Each report includes input, cached-input, and output token counts plus an estimated Luna API cost.
- Results are also saved to `agent.log`. Be warned, I like my log files a bit on the verbose side.



## Why this approach?
Instead of relying on fragile HTML parsing that breaks whenever a website updates its design, this script uses **Playwright** to open a real browser window and an **OpenAI multimodal model** to "look" at a screenshot of the page. It's resilient, easy to adapt to any website, and cost-sensitive to run. I initially started out parsing the page and it got messy and complicated very quickly. I tried this method and it was cut and dry and simple to implement. Using the vision method also means now I can share it and you can potentially adapt it to other retailers.

## Things to keep in mind

- You need to be just a tiny bit comfortable working in the terminal to get this set up.
- It's Windows only at the moment but could be adapted to Mac pretty easily. Just give the `README.md`, `visual-product-agent.py`, and `.env.example` files to an AI model and tell it you need to make it work on a Mac instead of Windows and to include updating instructions in the README.
- You can also adapt it pretty easily to any other product or web site as I am pretty sure you aren't interested in the exact jeans I am. Mostly the same drill as above, give it the specific product URLs and tell it it needs to update the URLs as well as the prompt text in `visual-product-agent.py`.
- HOWEVER, using it on other websites only works if each product you want status on has a unique URL. 
- You cannot have the Chrome browser open when this is running. Playwright will install a test version of Chrome and use that to get the product status. You might have to log into the account of the website you are going to, which should become obvious to you as you test it. Also, don't worry, it doesn't even have a trace of the tools needed to order items without your okay.
- As the code exists now, you can watch the agent open a Chrome window and navigate to the page(s) you are interested in, then it closes it. I liked it for testing and just to watch it run. You can change that so it runs in the background (headless) by changing `headless=False` to `headless=True`.


<a id="setup-start"></a>
------

##### The setup notes below are AI-assisted, fact checked by a human, and kept intentionally brief.

## Prerequisites
- Python 3.8+
- An OpenAI API key
- A Gmail account with an App Password generated (for sending emails)
- Google Chrome installed

## Setup Instructions

### 1. Install Dependencies
Install the required Python packages:
```bash
pip install playwright openai python-dotenv
playwright install chromium
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory of the project and add your credentials:

```ini
OPENAI_API_KEY=your_openai_api_key_here
SENDER_EMAIL=your_sending_gmail@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=where_to_send_report@example.com

# Chrome Profile Configuration
# On Windows, this is typically: C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data
CHROME_USER_DATA_DIR=C:\path\to\your\chrome\User Data
CHROME_PROFILE_NAME=Profile 1 # Or "Default", "Profile 2", etc.
```

*Note: Using a persistent Chrome profile allows the script to mimic your actual browser. Make sure all instances of Chrome using that specific profile are closed before running the script, otherwise Playwright will fail to launch it.*

### 3. Customize the Target URLs
Open the `visual-product-agent.py` file and modify the `URLS` dictionary. The key should be the target URL, and the value should be the product name or title you want to appear in the email report.

```python
URLS = {
    "https://example.com/product/123": "My Favorite Product",
    "https://example.com/product/456": "Another Product"
}
```

### 4. Customize the Prompt 
If you are scraping something other than Old Navy, update the prompt sent to the OpenAI model. The relevant call in `visual-product-agent.py` looks like this:
```python
response = client.responses.create(
    model="gpt-5.6-luna",
    reasoning={"effort": "high"},
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Your product-analysis instructions..."},
            {"type": "input_image", "image_url": image_data_url, "detail": "high"}
        ]
    }]
)
```
Adjust the `input_text` instruction to ask the model for whatever information is relevant to the page you are scraping.

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
- The script preserves the last captured screenshot as `temp_price_shot.png` in the directory. This is useful for debugging if the script encounters a navigation error or if the model returns unexpected results.
- All actions, errors, and rate limit retries are logged to `agent.log`.
