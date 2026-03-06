# Technical Project Specification: Denim Vision Agent (2026)

This comprehensive document serves as the "Source of Truth" for the **Denim Vision Agent** project. It is designed to bring a new developer or AI (like Antigravity IDE) from zero to full proficiency regarding the project's history, architecture, and current status.

------

## 1. Project Intent & "The North Star"

The objective is to create a lightweight, resilient automation agent that monitors the price and availability of specific apparel items at Old Navy.

**The "North Star" Principle:** The agent must behave like a human user. It should open a browser, look at the screen, and report what it sees. We have moved away from "backend" data scraping in favor of **AI Vision** to ensure the agent survives website redesigns and bypasses aggressive bot-protection.

------

## 2. The Target Parameters

- **Retailer:** Old Navy (Gap Inc.).
- **Product:** Men's Jeans.
- **Specific Variation:** Size **34W x 34L**.
- **URL-Specific Targeting:** We do **not** programmatically click size buttons. Instead, we use "variant-encoded" URLs where the size is pre-selected.
  - *Example URL 1:* `https://oldnavy.gap.com/browse/product.do?pid=5844620023434&vid=1#pdp-page-content`
  - *Example URL 2:* `https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1#pdp-page-content`
- **Required Data Points:**
  1. Current Price.
  2. Shipping Availability (Is it shippable to home?).
  3. In-Store Pickup Availability (Is it in stock at the local store?).

------

## 3. The "Wall of Failures" (Ruled-Out Paths)

To avoid repeating past mistakes, the following approaches have been tested and strictly ruled out:

| **Approach**                    | **Why it Failed**                                            |
| ------------------------------- | ------------------------------------------------------------ |
| **Traditional HTML Scraping**   | Old Navy uses Akamai bot-protection and dynamic CSS classes. The selectors change frequently, breaking the code. |
| **JSON/Data-Bootstrap Hunt**    | We attempted to find hidden JSON blobs (e.g., `__PRELOADED_STATE__`) to avoid opening a browser. The data was either obfuscated, incomplete, or blocked by security headers. |
| **`networkidle` Wait Trigger**  | Playwright’s standard `networkidle` wait timed out (30s+) because Old Navy’s site runs 100+ background trackers and ads that never stop "talking" to the network. |
| **`load` Wait Trigger**         | Even after the "load" event, price and stock elements often took an additional 2–3 seconds to "paint" on the screen, leading to blank screenshots. |
| **Standard/Incognito Browsing** | Defaulting to a clean browser state caused the site to lose the user's location, consistently reverting to the "Greece Ridge" store rather than the desired local store. |
| **Legacy Gemini SDKs**          | The `google-generativeai` library became unstable in early 2026. Using old model strings like `gemini-1.5-flash` often returned 404 "Not Found" errors in the newer environment. |

------

## 4. Technical Architecture (The "Vision-First" Stack)

### A. Browser Layer: Playwright (Sync)

The agent uses Playwright to drive a real Google Chrome instance.

- **Persistent Profile:** The agent **must** use the user's actual `Default` Chrome profile directory. This carries the cookies and session data that fix the store location and bypass "New User" pop-ups.
- **The "Human Wait" Logic:** Instead of listening to code-level events, the script uses a `commit` trigger (to ensure the URL has resolved) followed by a **hard 7-second `time.sleep`**. This guarantees the visual UI is fully rendered before the "camera" clicks.

### B. Intelligence Layer: Gemini 2.0 Flash

The screenshot is analyzed by the `google-genai` (v2026) SDK.

- **Model:** `gemini-2.0-flash`.

- **Prompting Strategy:** We use a strict extraction prompt to minimize AI "chatter":

  > *"Look at this Old Navy product page. What is the current price? Is it available for shipping? Is it available for in-store pickup? Return only: Price: [value], Shipping: [Available/Unavailable], Pickup: [Available/Unavailable]"*

### C. Communication Layer: SMTP (Gmail)

- **Frequency:** Every single run (The "Heartbeat" policy).
- **Purpose:** Verification that the script successfully navigated, captured, and analyzed the data.
- **Security:** Utilizes a 16-digit Google **App Password**. 2-Step Verification must be enabled on the sender account (`fidoalert@gmail.com`).

------

## 5. Hardware & Environment Specs

- **Primary Development:** Gateway Gaming Laptop (Windows 11, Intel i7, 16GB RAM).
- **Final Destination:** Beelink Mini S12 (MiniS) PC (Intel N95, 8GB RAM).
  - *Note:* Because the Beelink has an N95 processor, we use **Headless** mode to conserve resources, but **Vision** is still preferred over JSON because it's more maintainable.
- **Task Management:** Triggered via **Windows Task Scheduler**.
- **Critical Constraint:** Google Chrome **must be closed** for the script to run. If Chrome is open, the Profile Data folder is locked and Playwright will crash.

------

## 6. Current Script Logic (test-agent-ai.py)

The script follows this linear execution:

1. Initialize `genai.Client` with 2026 SDK.
2. Launch Playwright `launch_persistent_context` using the Chrome `User Data` path.
3. Loop through target URLs:
   - Navigate (`wait_until="commit"`).
   - Wait 7 seconds (Visual Settle).
   - Take Screenshot (`page.screenshot`).
   - Convert image to bytes.
   - Request Vision Analysis from `gemini-2.0-flash`.
4. Aggregate results.
5. Send formatted Email via `smtplib`.
6. Close Browser Context.

------

## 7. Setup Requirements for AG / New Environments

1. **Libraries:** `pip install -U playwright google-genai`
2. **Browsers:** `playwright install chrome`
3. **Chrome Path:** Identify the local path to `AppData\Local\Google\Chrome\User Data`.
4. **Credentials:**
   - `GEMINI_API_KEY`: A valid Google AI Studio key.
   - `EMAIL_APP_PASSWORD`: A 16-digit code from Google Account Security.

------

**Status:** The browser automation and visual capture logic are verified. The current focus is ensuring the 2026 SDK (`google-genai`) and the `gemini-2.0-flash` model are correctly integrated to avoid 404 errors.