import requests
import re

# Use the specific Old Navy URL for your jeans here
url = "https://oldnavy.gap.com/browse/product.do?pid=5844470023434&vid=1&pcid=1031099&cid=1031099&nav=meganav%3AMen%3A%3A#pdp-page-contentE"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"Fetching {url}...")
response = requests.get(url, headers=headers)
html = response.text

# This looks for any script tag that contains 'inventory' 
# and prints the first 200 characters of that tag.
print("\n--- Potential Data Blocks Found ---")
matches = re.findall(r'<script[^>]*>(.*?)inventory(.*?)</script>', html, re.DOTALL | re.IGNORECASE)

if matches:
    for i, match in enumerate(matches):
        # We look at the beginning of the script to find the variable name
        content = match[0] + "inventory" + match[1]
        snippet = content.strip()[:300]
        print(f"\nBlock #{i+1} Snippet:")
        print(f"{snippet}...")
else:
    print("No script tags found containing 'inventory'. Checking for hidden JSON IDs...")
    # Sometimes it's in a <script id="some-id" type="application/json">
    json_blocks = re.findall(r'<script type="application/json" id="(.*?)">(.*?)</script>', html, re.DOTALL)
    for j_id, j_content in json_blocks:
        if "inventory" in j_content:
            print(f"Found inventory in JSON block with ID: {j_id}")