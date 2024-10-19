from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import requests
import json
import pyautogui
import time

def get_openai_summary(text, api_key):
    """Generates a summary for the given text using OpenAI API."""
    openai_url = "https://api.openai.com/v1/engines/davinci-codex/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "prompt": f"Summarize this: \"{text}\"",
        "max_tokens": 60
    }
    response = requests.post(openai_url, headers=headers, json=data)
    summary = response.json()['choices'][0]['text'].strip()
    return summary

# Define the path to your JSON file (this will be different on a different device)
json_file_path = r'O:\coding\python\gitstuff\NOSHARING\open_ai-api-key.json'

# Load the API key from the JSON file
with open(json_file_path, 'r') as file:
    data = json.load(file)
    openai_api_key = data.get("hulme_summarizer_key")
    
# Setup Selenium WebDriver
driver_path = r"O:\Coding\python\selenium\chromedriver\win64-120.0.6099.109\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# Navigate to a news website
driver.get("https://www.bbc.com/news")

# Extract the headline of the top news article
time.sleep(5)  # Wait for the page to load
headline_element = driver.find_element_by_css_selector("h2[data-testid='card-headline']")
headline = headline_element.text

# Use OpenAI to generate a summary of the headline
summary = get_openai_summary(headline, openai_api_key)

print(f"Headline: {headline}")
print(f"Summary: {summary}")

# Close the browser
driver.quit()
