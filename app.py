import requests
from instagrapi import Client
from flask import Flask, request, render_template_string
import time
import random
import os
import json
from datetime import datetime
from fake_useragent import UserAgent
import os

# Configurações
SESSION_FOLDER = "sessions"
BLOCKS_FILE = "account_blocks.json"
if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

# Função para gerar cabeçalhos com user-agent aleatório
def get_random_headers():
    ua = UserAgent()
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

# Função para configurar proxy no cliente
def set_client_proxy(client, proxy):
    if proxy:
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        client.set_proxy(proxy_dict)
    return client

# Função para logar ou carregar uma sessão existente
def get_client(username, password, proxy=None):
    session_file = os.path.join(SESSION_FOLDER, f"{username}_session.json")
    cl = Client()
    cl.request.headers.update(get_random_headers())
    if proxy:
        cl = set_client_proxy(cl, proxy)
    
    try:
        if os.path.exists(session_file):
            cl.load_settings(session_file)
            print(f"Sessão carregada com sucesso para {username}.")
            return cl
        cl.login(username, password)
        cl.dump_settings(session_file)
        print(f"Login realizado e sessão salva para {username}.")
        return cl
    except Exception as e:
        error_message = str(e)
        if "BadPassword" in error_message:
            print(f"Erro: Senha incorreta para {username}.")
            return f"Erro: Senha incorreta para {username}."
        elif "ChallengeRequired" in error_message:
            print(f"Erro: A conta {username} requer verificação adicional.")
            return f"Erro: Verificação adicional necessária para {username}."
        elif "We can send you an email" in error_message:
            print(f"Erro: A conta {username} está bloqueada.")
            return f"Erro: Conta {username} bloqueada. Recupere por e-mail."
        else:
            print(f"Erro desconhecido para {username}: {error_message}")
            return f"Erro desconhecido: {error_message}"

# Função para comentar em uma publicação
def comment_post(client, post_url, comment, proxy=None):
    try:
        if proxy:
            client = set_client_proxy(client, proxy)
        media_id = client.media_pk_from_url(post_url)
        if not media_id:
            print(f"Erro: Não foi possível obter o ID da mídia para {post_url}.")
            return False
        client.media_comment(media_id, comment)
        print(f"Comentário enviado: {comment}")
        time.sleep(random.uniform(5, 15))
        return True
    except Exception as e:
        print(f"Erro ao comentar na publicação {post_url}: {e}")
        return False

# Função para carregar ou salvar blocos de contas
def load_account_blocks():
    if os.path.exists(BLOCKS_FILE):
        with open(BLOCKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_account_blocks(blocks):
    with open(BLOCKS_FILE, "w") as f:
        json.dump(blocks, f, indent=4)

# Comentários aleatórios
COMMENTS = [
    "Post incrível! 👏",
    "Amei o conteúdo! 😍",
    "Muito inspirador, parabéns! 🌟",
    "Adorei essa postagem! 💖",
    "Conteúdo de qualidade, continue assim! 💡",
    "Isso é maravilhoso! 🙌",
    "Tão criativo, adorei! 🎨",
    "Excelente trabalho! 🚀",
    "Muito interessante, adorei! 📚",
    "Simplesmente incrível! 🌈"
]

# Configuração do Flask
app = Flask(__name__)

# Rotas
@app.route("/panel", methods=["GET"])
def panel():
    with open('templates/login.html', 'r') as file:
        return file.read()

@app.route("/enviar", methods=["GET"])
def enviar():
    with open('templates/enviar.html', 'r') as file:
        return file.read()

@app.route("/manual-login", methods=["POST"])
def manual_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    proxy = data.get("proxy")

    try:
        blocks = load_account_blocks()
        proxy_exists = False
        target_block = None

        for block in blocks:
            if block["proxy"] == proxy:
                proxy_exists = True
                if len(block["accounts"]) < 5:
                    target_block = block
                else:
                    return f"Erro: O proxy {proxy} já atingiu o limite de 5 contas."
        
        if not proxy_exists and proxy:
            target_block = {"proxy": proxy, "accounts": []}
            blocks.append(target_block)
        
        client = get_client(username, password, proxy)
        if isinstance(client, str):
            return client
        if client is None:
            return f"Erro: Não foi possível realizar login para {username}."

        if target_block:
            target_block["accounts"].append({"username": username, "password": password})
            save_account_blocks(blocks)
        
        return f"Login realizado com sucesso para {username}."
    except Exception as e:
        return f"Erro desconhecido ao realizar login para {username}: {e}"

@app.route("/file-login", methods=["POST"])
def file_login():
    file = request.files.get("file")
    if not file:
        return "Erro: Nenhum arquivo enviado."

    try:
        data = json.load(file)
        blocks = load_account_blocks()
        
        for account in data:
            username = account.get("username")
            password = account.get("password")
            proxy = account.get("proxy")

            if not username or not password:
                continue

            proxy_exists = False
            target_block = None
            for block in blocks:
                if block["proxy"] == proxy:
                    proxy_exists = True
                    if len(block["accounts"]) < 5:
                        target_block = block
                    else:
                        return f"Erro: O proxy {proxy} já atingiu o limite de 5 contas."
            
            if not proxy_exists and proxy:
                target_block = {"proxy": proxy, "accounts": []}
                blocks.append(target_block)
            
            client = get_client(username, password, proxy)
            if isinstance(client, str):
                continue
            
            if target_block:
                target_block["accounts"].append({"username": username, "password": password})
        
        save_account_blocks(blocks)
        return "Contas importadas e logadas com sucesso!"
    except Exception as e:
        return f"Erro ao importar contas: {e}"

@app.route("/send-comments", methods=["POST"])
def send_comments():
    data = request.get_json()
    post_url = data.get("post_url")
    quantity = int(data.get("quantity"))

    blocks = load_account_blocks()
    if not blocks:
        return "Erro: Nenhuma conta está logada para enviar comentários."

    comments_sent = 0
    used_accounts = []

    for block in blocks:
        if comments_sent >= quantity:
            break
        proxy = block.get("proxy")
        for account in block["accounts"]:
            if comments_sent >= quantity:
                break
            username = account["username"]
            if username in used_accounts:
                continue

            try:
                cl = Client()
                cl.request.headers.update(get_random_headers())
                cl.load_settings(os.path.join(SESSION_FOLDER, f"{username}_session.json"))
                print(f"Sessão carregada para {username}. Enviando comentário...")

                comment = random.choice(COMMENTS)
                success = comment_post(cl, post_url, comment, proxy)
                
                if success:
                    comments_sent += 1
                    used_accounts.append(username)
                    print(f"Comentário enviado pela conta {username} com proxy {proxy}.")
                else:
                    print(f"Falha ao enviar comentário pela conta {username}.")
            except Exception as e:
                print(f"Erro ao carregar sessão para {username}: {e}")
                continue

    return f"{comments_sent} comentários enviados para {post_url} com sucesso!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)