
from flask import Flask, jsonify
import requests
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
import os

app = Flask(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
] * 10  # encurtado para espaço

request_counter = 0
current_user_agent_index = 0

def get_user_agent():
    global current_user_agent_index
    return USER_AGENTS[current_user_agent_index]

def update_user_agent():
    global request_counter, current_user_agent_index
    request_counter += 1
    if request_counter % 5 == 0:
        current_user_agent_index = (current_user_agent_index + 1) % len(USER_AGENTS)

def extract_username_from_url(profile_url):
    pattern = r"https?://www\\.instagram\\.com/([^/]+)/?"
    match = re.match(pattern, profile_url)
    if match:
        return match.group(1)
    return profile_url

def get_instagram_profile_selenium(profile_url):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument(f"user-agent={get_user_agent()}")
        driver = webdriver.Chrome(options=options)

        driver.get(profile_url)
        time.sleep(3)
        html = driver.page_source.lower()
        flagged = any(x in html for x in ["under review", "restricted", "flagged", "temporarily unavailable"])
        driver.quit()
        update_user_agent()
        return {"html_length": len(html), "flagged": flagged}
    except Exception as e:
        update_user_agent()
        return {"error": str(e)}

def get_instagram_profile_direct(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/json",
        "Referer": f"https://www.instagram.com/{username}/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_instagram_profile(profile_url):
    username = extract_username_from_url(profile_url)
    result = get_instagram_profile_selenium(profile_url)
    if "error" not in result:
        return result
    return get_instagram_profile_direct(username)

@app.route('/profile/<path:profile_url>')
def show_profile(profile_url):
    if not profile_url.startswith(('http://', 'https://')):
        profile_url = f"https://{profile_url}"
    data = get_instagram_profile(profile_url)
    return jsonify(data)

if __name__ == '__main__':
    host = '0.0.0.0' if os.environ.get("RENDER") else '127.0.0.1'
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port)
