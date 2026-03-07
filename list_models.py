import os
from google import genai

GEMINI_API_KEY = "AIzaSyDv5Mwj8rxqDSsQbGmy0SRrapB-Ir-JJJo" 
client = genai.Client(api_key=GEMINI_API_KEY)

for model in client.models.list():
    if "flash" in model.name.lower() or "gemini" in model.name.lower():
        print(model.name)
