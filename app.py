import os
import json
import time
import random
from datetime import datetime, timedelta
from instagrapi import Client
from flask import Flask, request, render_template, redirect, url_for, jsonify, session, flash

# Configurações
SESSION_FOLDER = "sessions"
ORDERS_FOLDER = "orders"
GROUPS_FOLDER = "groups"
DEVICES_FILE = "devices.json"
API_KEY = "96b16ebae1c61067bb25fe62"  # Chave de API de 22 dígitos
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Em produção, use uma senha forte e hash

# Listas de emojis e comentários
POSITIVE_EMOJI_COMMENTS = ["👍", "❤️", "🔥", "👏", "😎", "🎉", "😍", "🙌", "🤩", "✨", "🌟", "💖", "🥳", "💯", "😊"]
NEGATIVE_EMOJI_COMMENTS = ["😒", "👎", "😣", "🙄", "😞", "😕", "😢", "🤬", "😓", "😑", "💔", "😠", "🤦", "😤", "😖"]
POSITIVE_TEXT_COMMENTS = [
    "Ótimo conteúdo!", "Parabéns, adorei!", "Muito bom!", "Incrível!", "Top demais!", "Amei isso!", "Excelente trabalho!", "Você arrasou!", "Fantástico!"
]
NEGATIVE_TEXT_COMMENTS = [
    "Não gostei muito.", "Poderia melhorar.", "Esperava mais.", "Não curti.", "Deixou a desejar.", "Muito fraco.", "Nada interessante.", "Que decepção.", "Péssimo."
]

# Serviços disponíveis
SERVICES = {
    "1": "Instagram Comentários Positivos (Emojis) | Brazil ★ R30 | Max 6K | Start: 15m",
    "2": "Instagram Comentários Negativos (Emojis) | Brazil ★ R30 | Max 6K | Start: 15m",
    "3": "Instagram Comentários Personalizados | Brazil ★ R30 | Max 6K | Start: 15m",
    "4": "Instagram Comentários Positivos (Texto) | Brazil ★ R30 | Max 6K | Start: 15m",
    "5": "Instagram Comentários Negativos (Texto) | Brazil ★ R30 | Max 6K | Start: 15m",
    "6": "Instagram Comentários Positivos (Emojis + Texto) | Brazil ★ R35 | Max 6K | Start: 15m",
    "7": "Instagram Comentários Negativos (Emojis + Texto) | Brazil ★ R35 | Max 6K | Start: 15m",
    "8": "Instagram Comentários Aleatórios (Emojis) | Brazil ★ R25 | Max 6K | Start: 15m",
    "9": "Instagram Comentários Aleatórios (Texto) | Brazil ★ R25 | Max 6K | Start: 15m"
}

# Criar pastas se não existirem
for folder in [SESSION_FOLDER, ORDERS_FOLDER, GROUPS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Carregar dispositivos padrão se o arquivo não existir
if not os.path.exists(DEVICES_FILE):
    default_devices = [
        {
            "name": "iPhone 13 Pro",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "480dpi",
                "resolution": "1170x2532",
                "manufacturer": "Apple",
                "device": "iPhone13,3",
                "model": "iPhone 13 Pro",
                "cpu": "A15",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 iPhone (iPhone13,3; iOS 15_4; en_US; en-US; scale=3.00; 1170x2532; 386066785)"
            }
        },
        {
            "name": "Samsung Galaxy S21",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 30,
                "android_release": "11.0",
                "dpi": "420dpi",
                "resolution": "1080x2400",
                "manufacturer": "Samsung",
                "device": "SM-G991B",
                "model": "Galaxy S21",
                "cpu": "Exynos 2100",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (30/11.0; 420dpi; 1080x2400; Samsung; SM-G991B; Galaxy S21; Exynos 2100; en_US; 314665256)"
            }
        },
        {
            "name": "Google Pixel 6",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 31,
                "android_release": "12.0",
                "dpi": "440dpi",
                "resolution": "1080x2400",
                "manufacturer": "Google",
                "device": "Pixel 6",
                "model": "Pixel 6",
                "cpu": "Google Tensor",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (31/12.0; 440dpi; 1080x2400; Google; Pixel 6; Pixel 6; Google Tensor; en_US; 314665256)"
            }
        },
        {
            "name": "OnePlus 9 Pro",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 29,
                "android_release": "10.0",
                "dpi": "480dpi",
                "resolution": "1440x3168",
                "manufacturer": "OnePlus",
                "device": "LE2125",
                "model": "OnePlus 9 Pro",
                "cpu": "Snapdragon 888",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (29/10.0; 480dpi; 1440x3168; OnePlus; LE2125; OnePlus 9 Pro; Snapdragon 888; en_US; 314665256)"
            }
        },
        {
            "name": "Xiaomi Mi 11",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 30,
                "android_release": "11.0",
                "dpi": "440dpi",
                "resolution": "1440x3200",
                "manufacturer": "Xiaomi",
                "device": "M2011K2G",
                "model": "Mi 11",
                "cpu": "Snapdragon 888",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (30/11.0; 440dpi; 1440x3200; Xiaomi; M2011K2G; Mi 11; Snapdragon 888; en_US; 314665256)"
            }
        },
        {
            "name": "MacBook Pro Chrome",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "device_type": "desktop"
            }
        },
        {
            "name": "Windows 10 Firefox",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
                "device_type": "desktop"
            }
        },
        {
            "name": "iPad Pro",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "device_type": "tablet"
            }
        },
        {
            "name": "Samsung Galaxy Tab S7",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 30,
                "android_release": "11.0",
                "dpi": "320dpi",
                "resolution": "1600x2560",
                "manufacturer": "Samsung",
                "device": "SM-T870",
                "model": "Galaxy Tab S7",
                "cpu": "Snapdragon 865+",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (30/11.0; 320dpi; 1600x2560; Samsung; SM-T870; Galaxy Tab S7; Snapdragon 865+; en_US; 314665256)"
            }
        },
        {
            "name": "Huawei P40 Pro",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 29,
                "android_release": "10.0",
                "dpi": "480dpi",
                "resolution": "1200x2640",
                "manufacturer": "Huawei",
                "device": "ELS-NX9",
                "model": "P40 Pro",
                "cpu": "Kirin 990",
                "version_code": "314665256",
                "user_agent": "Instagram 269.0.0.18.75 Android (29/10.0; 480dpi; 1200x2640; Huawei; ELS-NX9; P40 Pro; Kirin 990; en_US; 314665256)"
            }
        }
    ]
    with open(DEVICES_FILE, 'w') as f:
        json.dump(default_devices, f, indent=4)

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_aqui'

# Funções auxiliares
def generate_token():
    return ''.join(random.choices('0123456789abcdef', k=22))

def get_available_devices():
    with open(DEVICES_FILE, 'r') as f:
        return json.load(f)

def get_random_device():
    devices = get_available_devices()
    return random.choice(devices)

def save_session_to_group(group_name, sessionid, ds_user_id, proxy=None, proxy_type=None):
    try:
        cl = Client()
        group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
        if os.path.exists(group_file):
            with open(group_file, 'r') as f:
                group_data = json.load(f)
            device_settings = group_data.get('device_settings', {})
        else:
            device = get_random_device()
            device_settings = device['device_settings']
            group_data = {
                'name': group_name,
                'device_settings': device_settings,
                'accounts': [],
                'proxy': proxy,
                'proxy_type': proxy_type
            }
            with open(group_file, 'w') as f:
                json.dump(group_data, f, indent=4)
        
        settings = {
            "authorization_data": {"ds_user_id": ds_user_id, "sessionid": sessionid},
            "user_agent": device_settings.get('user_agent', "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T Dev; devitron; qcom; en_US; 314665256)"),
            "device_settings": device_settings
        }
        
        if proxy:
            settings["proxy"] = proxy
        
        cl.set_settings(settings)
        info = cl.account_info()
        username = info.username
        
        group_data = {}
        if os.path.exists(group_file):
            with open(group_file, 'r') as f:
                group_data = json.load(f)
        
        accounts = group_data.get('accounts', [])
        if len(accounts) >= 5:
            return False, "Este grupo já atingiu o limite máximo de 5 contas."
        
        for account in accounts:
            if account['username'] == username:
                return False, "Esta conta já foi adicionada a este grupo."
        
        accounts.append({
            'username': username,
            'ds_user_id': ds_user_id,
            'sessionid': sessionid,
            'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        group_data['accounts'] = accounts
        with open(group_file, 'w') as f:
            json.dump(group_data, f, indent=4)
        
        session_file = os.path.join(SESSION_FOLDER, f"{username}_session.json")
        cl.dump_settings(session_file)
        
        print(f"✅ Login bem-sucedido para @{username} no grupo {group_name}")
        return True, username
    
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {str(e)}"
        print(f"❌ Erro ao validar sessão: {error_message}")
        return False, error_message

def comment_post(client, post_url, comment, service_id):
    try:
        media_id = client.media_pk_from_url(post_url)
        if not media_id:
            print(f"Erro: Não foi possível obter o ID da mídia para {post_url}.")
            return False, "Não foi possível obter o ID da mídia."
        client.media_comment(media_id, comment)
        print(f"Comentário enviado: {comment} (Serviço ID: {service_id})")
        return True, ""
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {str(e)}"
        print(f"Erro ao comentar na publicação {post_url}: {error_message}")
        return False, error_message

def validate_api_key(key):
    return key == API_KEY and len(key) == 22

def get_next_order_id():
    order_files = [f for f in os.listdir(ORDERS_FOLDER) if f.startswith("order_") and f.endswith(".json")]
    return max([int(f.split("_")[1].split(".")[0]) for f in order_files] + [0]) + 1

def create_order(link, quantity, username, service_id, custom_comments=None):
    order_id = get_next_order_id()
    order = {
        "id": order_id,
        "user": username,
        "charge": round(random.uniform(0.1, 0.3), 3),
        "link": link,
        "start_count": 0,
        "quantity": quantity,
        "service_id": service_id,
        "service": SERVICES.get(service_id, "Serviço Desconhecido"),
        "status": "pending",
        "remains": None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "Auto",
        "custom_comments": custom_comments if custom_comments else None
    }
    with open(os.path.join(ORDERS_FOLDER, f"order_{order_id}.json"), 'w') as f:
        json.dump(order, f)
    return order_id

def get_order(order_id):
    file_path = os.path.join(ORDERS_FOLDER, f"order_{order_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def update_order(order_id, updates):
    order = get_order(order_id)
    if order:
        order.update(updates)
        with open(os.path.join(ORDERS_FOLDER, f"order_{order_id}.json"), 'w') as f:
            json.dump(order, f)
        return True
    return False

def list_orders(search_query=None):
    orders = []
    for file in os.listdir(ORDERS_FOLDER):
        if file.startswith("order_") and file.endswith(".json"):
            with open(os.path.join(ORDERS_FOLDER, file), 'r') as f:
                order = json.load(f)
                if search_query:
                    search_lower = search_query.lower()
                    if (str(order["id"]) == search_query or
                        order["link"].lower().find(search_lower) != -1 or
                        order["status"].lower() == search_lower):
                        orders.append(order)
                else:
                    orders.append(order)
    return sorted(orders, key=lambda x: x["id"], reverse=True)

def get_stats(period):
    current_date = datetime.now()
    if period == "daily":
        start_date = datetime.strptime(current_date.strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(current_date.strftime("%Y-%m-%d 23:59:59"), "%Y-%m-%d %H:%M:%S")
    elif period == "weekly":
        start_date = current_date - timedelta(days=current_date.weekday())
        start_date = datetime.strptime(start_date.strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
    else:  # monthly
        start_date = current_date.replace(day=1, hour=0, minute=0, second=0)
        end_date = (start_date + timedelta(days=31)).replace(day=1, hour=0, minute=0, second=0) - timedelta(seconds=1)
    
    stats = {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "canceled": 0,
        "partial": 0
    }
    
    for order in list_orders():
        order_date = datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S")
        if start_date <= order_date <= end_date:
            stats["total"] += 1
            stats[order["status"]] = stats.get(order["status"], 0) + 1
    
    return stats

def list_groups():
    groups = []
    for file in os.listdir(GROUPS_FOLDER):
        if file.endswith('.json'):
            with open(os.path.join(GROUPS_FOLDER, file), 'r') as f:
                group_data = json.load(f)
                groups.append({
                    'name': group_data['name'],
                    'device': group_data['device_settings'].get('name', 'Dispositivo Personalizado'),
                    'accounts_count': len(group_data.get('accounts', [])),
                    'proxy': group_data.get('proxy', 'Nenhum'),
                    'proxy_type': group_data.get('proxy_type', 'Nenhum')
                })
    return groups

def get_group_details(group_name):
    group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
    if os.path.exists(group_file):
        with open(group_file, 'r') as f:
            return json.load(f)
    return None

def create_group(group_name, proxy=None, proxy_type=None):
    group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
    if os.path.exists(group_file):
        return False, "Um grupo com este nome já existe."
    
    device = get_random_device()
    group_data = {
        'name': group_name,
        'device_settings': device['device_settings'],
        'accounts': [],
        'proxy': proxy,
        'proxy_type': proxy_type
    }
    
    with open(group_file, 'w') as f:
        json.dump(group_data, f, indent=4)
    
    return True, "Grupo criado com sucesso."

def update_group(group_name, updates):
    group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
    if os.path.exists(group_file):
        with open(group_file, 'r') as f:
            group_data = json.load(f)
        group_data.update(updates)
        with open(group_file, 'w') as f:
            json.dump(group_data, f, indent=4)
        return True
    return False

def delete_group(group_name):
    group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
    if os.path.exists(group_file):
        with open(group_file, 'r') as f:
            group_data = json.load(f)
            for account in group_data.get('accounts', []):
                session_file = os.path.join(SESSION_FOLDER, f"{account['username']}_session.json")
                if os.path.exists(session_file):
                    os.remove(session_file)
        os.remove(group_file)
        return True, "Grupo removido com sucesso."
    return False, "Grupo não encontrado."

def remove_account_from_group(group_name, username):
    group_file = os.path.join(GROUPS_FOLDER, f"{group_name}.json")
    if os.path.exists(group_file):
        with open(group_file, 'r') as f:
            group_data = json.load(f)
        accounts = group_data.get('accounts', [])
        updated_accounts = [acc for acc in accounts if acc['username'] != username]
        if len(updated_accounts) == len(accounts):
            return False, "Conta não encontrada no grupo."
        group_data['accounts'] = updated_accounts
        with open(group_file, 'w') as f:
            json.dump(group_data, f, indent=4)
        session_file = os.path.join(SESSION_FOLDER, f"{username}_session.json")
        if os.path.exists(session_file):
            os.remove(session_file)
        return True, "Conta removida com sucesso."
    return False, "Grupo não encontrado."

def get_total_accounts():
    total = 0
    for file in os.listdir(GROUPS_FOLDER):
        if file.endswith('.json'):
            with open(os.path.join(GROUPS_FOLDER, file), 'r') as f:
                group_data = json.load(f)
                total += len(group_data.get('accounts', []))
    return total

# Rotas de Autenticação
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciais inválidas', 'error')
    
    return render_template('index.html', page='login')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Painel Administrativo
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    period = request.args.get('period', 'daily')
    search_query = request.args.get('search', '')
    stats = get_stats(period)
    orders = list_orders(search_query)
    logged_accounts = get_total_accounts()
    
    return render_template('index.html', page='dashboard', stats=stats, orders=orders, logged_accounts=logged_accounts, datetime=datetime)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    search_query = request.args.get('search', '')
    orders = list_orders(search_query)
    
    return render_template('index.html', page='orders', orders=orders, search_query=search_query, logged_accounts=get_total_accounts(), datetime=datetime)

@app.route('/admin/groups')
def admin_groups():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    groups = list_groups()
    
    return render_template('index.html', page='groups', groups=groups, datetime=datetime)

@app.route('/admin/group/<group_name>')
def admin_group_details(group_name):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group = get_group_details(group_name)
    if not group:
        flash('Grupo não encontrado', 'error')
        return redirect(url_for('admin_groups'))
    
    return render_template('index.html', page='group_details', group=group, total_groups=len(list_groups()), datetime=datetime)

@app.route('/admin/edit_group/<group_name>', methods=['GET', 'POST'])
def edit_group(group_name):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group = get_group_details(group_name)
    if not group:
        flash('Grupo não encontrado', 'error')
        return redirect(url_for('admin_groups'))
    
    if request.method == 'POST':
        new_group_name = request.form.get('group_name', '').strip()
        proxy_type = request.form.get('proxy_type', '').strip()
        proxy = request.form.get('proxy', '').strip() if proxy_type != 'none' else None
        
        if not new_group_name:
            flash('Nome do grupo é obrigatório.', 'error')
        else:
            updates = {
                'name': new_group_name,
                'proxy': proxy,
                'proxy_type': proxy_type if proxy_type != 'none' else None
            }
            if update_group(group_name, updates):
                if new_group_name != group_name:
                    os.rename(
                        os.path.join(GROUPS_FOLDER, f"{group_name}.json"),
                        os.path.join(GROUPS_FOLDER, f"{new_group_name}.json")
                    )
                flash('Grupo atualizado com sucesso.', 'success')
            else:
                flash('Falha ao atualizar grupo.', 'error')
        return redirect(url_for('admin_groups'))
    
    return render_template('index.html', page='edit_group', group=group, datetime=datetime)

@app.route('/admin/send', methods=['GET', 'POST'])
def admin_send():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    logged_accounts = get_total_accounts()
    
    if request.method == 'POST':
        post_url = request.form.get('post_url', '').strip()
        quantity = int(request.form.get('quantity', 1))
        service_id = request.form.get('service_id', '1')
        custom_comment = request.form.get('custom_comment', '').strip() if service_id == '3' else None
        
        if not post_url:
            flash('URL do post é obrigatória', 'error')
        elif logged_accounts == 0:
            flash('Nenhuma conta está logada para enviar comentários.', 'error')
        else:
            order_id = create_order(post_url, quantity, session.get('admin_username', 'admin'), service_id, custom_comment)
            comments_sent = 0
            error_logs = []
            update_order(order_id, {"status": "in_progress"})
            
            groups = []
            for file in os.listdir(GROUPS_FOLDER):
                if file.endswith('.json'):
                    with open(os.path.join(GROUPS_FOLDER, file), 'r') as f:
                        group_data = json.load(f)
                        groups.append(group_data)
            
            for group in groups:
                if comments_sent >= quantity:
                    break
                for account in group.get('accounts', []):
                    if comments_sent >= quantity:
                        break
                    username = account['username']
                    try:
                        cl = Client()
                        if group.get('proxy'):
                            cl.set_proxy(group['proxy'])
                        cl.set_settings({
                            "authorization_data": {
                                "ds_user_id": account['ds_user_id'],
                                "sessionid": account['sessionid']
                            },
                            "user_agent": group['device_settings'].get('user_agent', "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T Dev; devitron; qcom; en_US; 314665256)"),
                            "device_settings": group['device_settings']
                        })
                        cl.account_info()
                        
                        if service_id == '1':
                            comment = random.choice(POSITIVE_EMOJI_COMMENTS)
                        elif service_id == '2':
                            comment = random.choice(NEGATIVE_EMOJI_COMMENTS)
                        elif service_id == '3':
                            comment = custom_comment if custom_comment else random.choice(POSITIVE_TEXT_COMMENTS)
                        elif service_id == '4':
                            comment = random.choice(POSITIVE_TEXT_COMMENTS)
                        elif service_id == '5':
                            comment = random.choice(NEGATIVE_TEXT_COMMENTS)
                        elif service_id == '6':
                            comment = f"{random.choice(POSITIVE_TEXT_COMMENTS)} {random.choice(POSITIVE_EMOJI_COMMENTS)}"
                        elif service_id == '7':
                            comment = f"{random.choice(NEGATIVE_TEXT_COMMENTS)} {random.choice(NEGATIVE_EMOJI_COMMENTS)}"
                        elif service_id == '8':
                            comment = random.choice(POSITIVE_EMOJI_COMMENTS + NEGATIVE_EMOJI_COMMENTS)
                        elif service_id == '9':
                            comment = random.choice(POSITIVE_TEXT_COMMENTS + NEGATIVE_TEXT_COMMENTS)
                        else:
                            comment = random.choice(POSITIVE_EMOJI_COMMENTS)
                        
                        success, error_message = comment_post(cl, post_url, comment, service_id)
                        if success:
                            comments_sent += 1
                        else:
                            error_logs.append(f"Erro por @{username}: {error_message}")
                        
                        time.sleep(random.uniform(5, 10))
                    except Exception as e:
                        error_logs.append(f"Erro com @{username}: {str(e)}")
                        continue
            
            if comments_sent == 0:
                update_order(order_id, {"status": "canceled", "reason": ", ".join(error_logs) or "Verifique a URL ou os logs."})
                flash(f"Falha ao enviar comentários: {', '.join(error_logs)}", 'error')
            elif comments_sent < quantity:
                update_order(order_id, {"status": "partial", "remains": quantity - comments_sent})
                flash(f"Enviados {comments_sent}/{quantity} comentários. Erros: {', '.join(error_logs)}", 'warning')
            else:
                update_order(order_id, {"status": "completed"})
                flash(f"Sucesso! {comments_sent} comentários enviados.", 'success')
            
            return redirect(url_for('admin_orders'))
    
    return render_template('index.html', page='send', logged_accounts=logged_accounts, services=SERVICES, datetime=datetime)

@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('index.html', page='settings', logged_accounts=get_total_accounts(), 
         total_orders=len([f for f in os.listdir(ORDERS_FOLDER) if f.startswith('order_') and f.endswith('.json')]), 
         API_KEY=API_KEY, positive_emoji_comments=POSITIVE_EMOJI_COMMENTS, negative_emoji_comments=NEGATIVE_EMOJI_COMMENTS, 
         positive_text_comments=POSITIVE_TEXT_COMMENTS, negative_text_comments=NEGATIVE_TEXT_COMMENTS, datetime=datetime)

# Rotas para ações administrativas
@app.route('/admin/add_group', methods=['POST'])
def add_group():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group_name = request.form.get('group_name', '').strip()
    proxy_type = request.form.get('proxy_type', '').strip()
    proxy = request.form.get('proxy', '').strip() if proxy_type != 'none' else None
    
    if not group_name:
        flash('Nome do grupo é obrigatório.', 'error')
        return redirect(url_for('admin_groups'))
    
    success, result = create_group(group_name, proxy, proxy_type)
    if success:
        flash(result, 'success')
    else:
        flash(result, 'error')
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/delete_group', methods=['POST'])
def delete_group():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group_name = request.form.get('group_name', '').strip()
    if not group_name:
        flash('Nome do grupo não especificado.', 'error')
        return redirect(url_for('admin_groups'))
    
    success, result = delete_group(group_name)
    if success:
        flash(result, 'success')
    else:
        flash(result, 'error')
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/add_account_to_group/<group_name>', methods=['POST'])
def add_account_to_group(group_name):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    sessionid = request.form.get('sessionid', '').strip()
    ds_user_id = request.form.get('ds_user_id', '').strip()
    
    if not sessionid or not ds_user_id:
        flash('Ambos sessionid e ds_user_id são obrigatórios.', 'error')
        return redirect(url_for('admin_group_details', group_name=group_name))
    
    group = get_group_details(group_name)
    if not group:
        flash('Grupo não encontrado.', 'error')
        return redirect(url_for('admin_groups'))
    
    if len(group.get('accounts', [])) >= 5:
        flash('Este grupo já atingiu o limite máximo de 5 contas.', 'error')
        return redirect(url_for('admin_group_details', group_name=group_name))
    
    success, result = save_session_to_group(group_name, sessionid, ds_user_id, group.get('proxy'), group.get('proxy_type'))
    if success:
        flash(f'Conta @{result} adicionada com sucesso ao grupo {group_name}!', 'success')
    else:
        flash(f'Falha ao adicionar conta: {result}', 'error')
    
    return redirect(url_for('admin_group_details', group_name=group_name))

@app.route('/admin/remove_account_from_group', methods=['POST'])
def remove_account_from_group():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    group_name = request.form.get('group_name', '').strip()
    username = request.form.get('username', '').strip()
    
    if not group_name or not username:
        flash('Nome do grupo e usuário são obrigatórios.', 'error')
        return redirect(url_for('admin_groups'))
    
    success, result = remove_account_from_group(group_name, username)
    if success:
        flash(result, 'success')
    else:
        flash(result, 'error')
    
    return redirect(url_for('admin_group_details', group_name=group_name))

# API Endpoints
@app.route('/api/v2', methods=['POST'])
def api_v2():
    data = request.form or request.get_json()
    if not data:
        return jsonify({"status": "error", "error": "Nenhum dado fornecido"}), 400
    
    key = data.get('key')
    if not validate_api_key(key):
        return jsonify({"status": "error", "error": "Chave de API inválida"}), 401
    
    action = data.get('action')
    
    if action == 'getorder':
        order_id = data.get('type')
        order = get_order(order_id)
        if order:
            return jsonify({
                "status": "success",
                "id": order["id"],
                "user": order["user"],
                "charge": order["charge"],
                "link": order["link"],
                "start_count": order["start_count"],
                "quantity": order["quantity"],
                "service_id": order["service_id"],
                "service": order["service"],
                "status": order["status"],
                "remains": order["remains"],
                "created_at": order["created_at"],
                "mode": order["mode"],
                "custom_comments": order.get("custom_comments", None)
            })
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'setstartcount':
        order_id = data.get('id')
        start_count = data.get('start_count')
        if update_order(order_id, {"start_count": start_count}):
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'setcanceled':
        order_id = data.get('id')
        reason = data.get('reason', 'Cancelado pela API')
        if update_order(order_id, {"status": "canceled", "reason": reason}):
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'setpartial':
        order_id = data.get('id')
        remains = data.get('remains')
        if update_order(order_id, {"status": "partial", "remains": remains}):
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'setcompleted':
        order_id = data.get('id')
        if update_order(order_id, {"status": "completed"}):
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'updateOrders':
        orders = data.get('orders', [])
        results = []
        for order in orders:
            order_id = order.get('id')
            status = order.get('status')
            start_count = order.get('start_count')
            remains = order.get('remains')
            reason = order.get('reason', 'Atualizado pela API')
            updates = {}
            if status in ['pending', 'in_progress', 'processing', 'canceled', 'partial', 'completed']:
                updates["status"] = status
            if start_count is not None:
                updates["start_count"] = start_count
            if remains is not None:
                updates["remains"] = remains
            if status == "canceled":
                updates["reason"] = reason
            if updates:
                if update_order(order_id, updates):
                    results.append({"id": order_id, "status": "success"})
                else:
                    results.append({"id": order_id, "status": "error", "error": "Pedido não encontrado"})
            else:
                results.append({"id": order_id, "status": "error", "error": "Nenhuma atualização fornecida"})
        return jsonify({"status": "success", "results": results})
    
    elif action == 'getcancel':
        service_id = data.get('service_id')
        order = get_order(service_id)
        if order and order["status"] == "canceled":
            return jsonify({"status": "success", "cancel": order["id"]})
        return jsonify({"status": "error", "error": "Nenhum pedido cancelado encontrado"})
    
    elif action == 'setcancelrejected':
        task_id = data.get('cancel')
        if update_order(task_id, {"status": "pending", "reason": "Cancelamento rejeitado"}):
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": "Pedido não encontrado"})
    
    elif action == 'getstats':
        period = data.get('period', 'daily')
        stats = get_stats(period)
        return jsonify({"status": "success", "stats": stats})
    
    elif action == 'services':
        # Formatar a lista de serviços no formato esperado
        services_list = [
            {
                "service": service_id,
                "name": service_name,
                "type": "Default",
                "rate": service_name.split("★")[1].split("|")[0].strip() if "★" in service_name else "R30",
                "min": 1,
                "max": 6000,  # Baseado em "Max 6K"
                "category": "Instagram Comments",
                "custom_comments": True if service_id == "3" else False  # Apenas o serviço 3 permite comentários personalizados
            }
            for service_id, service_name in SERVICES.items()
        ]
        return jsonify(services_list)
    
    elif action == 'add':
        service_id = data.get('service')
        link = data.get('link')
        quantity = data.get('quantity')
        custom_comments = data.get('comments')  # Campo para comentários personalizados (usado no serviço 3)

        if not all([service_id, link, quantity]):
            return jsonify({"status": "error", "error": "Parâmetros obrigatórios ausentes (service, link, quantity)"}), 400
        
        if service_id not in SERVICES:
            return jsonify({"status": "error", "error": "Serviço inválido"}), 400
        
        try:
            quantity = int(quantity)
            if quantity < 1 or quantity > 6000:
                return jsonify({"status": "error", "error": "Quantidade fora dos limites (1-6000)"}), 400
        except ValueError:
            return jsonify({"status": "error", "error": "Quantidade deve ser um número válido"}), 400

        # Para o serviço personalizado (ID 3), validar e armazenar comentários personalizados
        if service_id == "3" and not custom_comments:
            return jsonify({"status": "error", "error": "Comentários personalizados são obrigatórios para este serviço"}), 400

        username = "api_user"  # Usuário padrão para pedidos via API
        order_id = create_order(link, quantity, username, service_id, custom_comments if service_id == "3" else None)
        return jsonify({"status": "success", "order": order_id})
    
    return jsonify({"status": "error", "error": "Ação inválida"})

# Rotas Públicas
@app.route('/login', methods=['GET', 'POST'])
def public_login():
    if request.method == 'POST':
        sessionid = request.form.get('sessionid', '').strip()
        ds_user_id = request.form.get('ds_user_id', '').strip()
        group_name = request.form.get('group_name', '').strip()
        
        if not sessionid or not ds_user_id:
            flash('Ambos sessionid e ds_user_id são obrigatórios.', 'error')
        else:
            success, result = save_session_to_group(group_name or 'default', sessionid, ds_user_id)
            if success:
                flash(f'Conta @{result} conectada com sucesso ao grupo {group_name or "default"}.', 'success')
            else:
                flash(f'Falha no login: {result}', 'error')
        
        return render_template('index.html', page='public_login', username=result if success else None, group_name=group_name or 'default')
    
    return render_template('index.html', page='public_login')

# Proteção contra acesso direto
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
