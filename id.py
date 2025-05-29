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

# Lista de user agents (mantida como no original)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    # ... (mantenha a lista completa do original)
] * 5

# Contador global de requisições
request_counter = 0
current_user_agent_index = 0

def get_user_agent():
    global current_user_agent_index
    user_agent = USER_AGENTS[current_user_agent_index]
    return user_agent

def update_user_agent():
    global request_counter, current_user_agent_index
    request_counter += 1
    if request_counter % 5 == 0:
        current_user_agent_index = (current_user_agent_index + 1) % len(USER_AGENTS)

def extract_username_from_url(profile_url):
    pattern = r"https?://www\.instagram\.com/([^/]+)/?"
    match = re.match(pattern, profile_url)
    if match:
        return match.group(1)
    return profile_url

def get_instagram_profile_selenium(profile_url):
    global request_counter
    username = extract_username_from_url(profile_url)
    if not username:
        return {"error": "Link inválido"}

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Nova flag headless para melhor compatibilidade
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")  # Reduz uso de memória compartilhada
        chrome_options.add_argument(f"user-agent={get_user_agent()}")
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(profile_url)
        time.sleep(3)

        script_content = driver.execute_script("return window._sharedData || {}")
        profile_info = {"error": "Dados não encontrados"}

        if script_content and "entry_data" in script_content and "ProfilePage" in script_content["entry_data"]:
            user_data = script_content["entry_data"]["ProfilePage"][0]["graphql"]["user"]
            profile_info = {
                "username": user_data.get("username", ""),
                "full_name": user_data.get("full_name", ""),
                "bio": user_data.get("biography", ""),
                "followers_count": user_data.get("edge_followed_by", {}).get("count", 0),
                "following_count": user_data.get("edge_follow", {}).get("count", 0),
                "post_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                "profile_picture_url": user_data.get("profile_pic_url_hd", user_data.get("profile_pic_url", "")),
                "website": user_data.get("external_url", ""),
                "is_verified": user_data.get("is_verified", False),
                "is_private": user_data.get("is_private", False),
                "is_business_account": user_data.get("is_business_account", False)
            }

        page_source = driver.page_source.lower()
        flagged = any(x in page_source for x in [
            "under review", "revisão", "restricted", "restrito", "flagged",
            "temporarily unavailable", "temporariamente indisponível"
        ])
        profile_info["is_flagged_for_review"] = flagged

        driver.quit()
        update_user_agent()
        return profile_info

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        update_user_agent()
        return {"error": f"Erro com Selenium: {str(e)}"}

def get_instagram_profile_direct(username):
    global request_counter
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.instagram.com/{username}/",
        "X-Requested-With": "XMLHttpRequest",
        "X-IG-App-ID": "936619743392459",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "user" in data["data"]:
            user = data["data"]["user"]
            profile_info = {
                "username": user.get("username", ""),
                "full_name": user.get("full_name", ""),
                "bio": user.get("biography", ""),
                "followers_count": user.get("edge_followed_by", {}).get("count", 0),
                "following_count": user.get("edge_follow", {}).get("count", 0),
                "post_count": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
                "profile_picture_url": user.get("profile_pic_url", ""),
                "website": user.get("external_url", ""),
                "is_verified": user.get("is_verified", False),
                "is_private": user.get("is_private", False),
                "is_business_account": user.get("is_business", False),
                "is_flagged_for_review": False
            }
            update_user_agent()
            return profile_info
        update_user_agent()
        return {"error": "Dados não encontrados na API direta"}
    except Exception as e:
        update_user_agent()
        return {"error": f"Erro na API direta: {str(e)}"}

def get_instagram_graphql_data(username):
    global request_counter
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={get_user_agent()}")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3)
        html = driver.page_source
        driver.quit()

        match = re.search(r"profilePage_(\d+)", html)
        if not match:
            update_user_agent()
            return {"error": "ID do usuário não encontrado"}
        user_id = match.group(1)

        query_hash = "ad99dd9d3646cc3c0dda65debcd266a7"
        variables = {
            "user_id": user_id,
            "include_reel": True,
            "fetch_mutual": False,
            "first": 50
        }

        graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={requests.utils.quote(json.dumps(variables))}"

        headers = {
            "User-Agent": get_user_agent(),
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{username}/"
        }

        response = requests.get(graphql_url, headers=headers, timeout=10)
        response.raise_for_status()
        update_user_agent()
        return response.json()

    except Exception as e:
        update_user_agent()
        return {"error": f"Erro no GraphQL: {str(e)}"}

def get_instagram_profile(profile_url):
    username = extract_username_from_url(profile_url)

    result = get_instagram_profile_selenium(profile_url)
    if "error" not in result:
        return result

    result = get_instagram_profile_direct(username)
    if "error" not in result:
        return result

    return get_instagram_graphql_data(username)

@app.route('/profile/<path:profile_url>')
def show_profile(profile_url):
    if not profile_url.startswith(('http://', 'https://')):
        profile_url = f"https://{profile_url}"
    profile_data = get_instagram_profile(profile_url)
    return jsonify(profile_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Usa a porta do Render ou 5000 localmente
    app.run(host='0.0.0.0', port=port, debug=False)  # Debug desativado para produção
