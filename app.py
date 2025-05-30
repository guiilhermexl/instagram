import os
import json
import time
import random
from datetime import datetime, timedelta
from instagrapi import Client
from flask import Flask, request, render_template_string, redirect, url_for, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash # Mantido para hash da senha do admin

# Configurações
SESSION_FOLDER = "sessions"
ORDERS_FOLDER = "orders"
GROUPS_FOLDER = "groups"
DEVICES_FILE = "devices.json"

# Valores fixos como no seu código original
API_KEY = "96b16ebae1c61067bb25fe62"  # Chave de API de 22 dígitos
EMOJI_COMMENTS = ["👍", "❤️", "🔥", "👏", "😎", "🎉", "😍", "🙌", "🤩", "✨"]
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # A senha em texto puro é usada aqui, conforme sua solicitação.

# Criar pastas se não existirem
# No Render (plano gratuito), estes arquivos serão efêmeros.
# Para persistência de dados, considere um banco de dados ou volumes persistentes.
if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)
if not os.path.exists(ORDERS_FOLDER):
    os.makedirs(ORDERS_FOLDER)
if not os.path.exists(GROUPS_FOLDER):
    os.makedirs(GROUPS_FOLDER)

# Carregar dispositivos padrão se o arquivo não existir
if not os.path.exists(DEVICES_FILE):
    default_devices = [
        {
            "name": "iPhone 13 Pro",
            "device_settings": {
                "app_version": "269.0.0.21.109",
                "android_version": "33",
                "android_release": "13",
                "dpi": "420dpi",
                "resolution": "1080x2400",
                "manufacturer": "Apple",
                "model": "iPhone14,2",
                "device": "iPhone14,2",
                "cpu": "arm64-v8a"
            }
        },
        {
            "name": "Samsung Galaxy S22",
            "device_settings": {
                "app_version": "270.0.0.12.112",
                "android_version": "33",
                "android_release": "13",
                "dpi": "480dpi",
                "resolution": "1440x3200",
                "manufacturer": "Samsung",
                "model": "SM-S901U",
                "device": "raven",
                "cpu": "arm64-v8a"
            }
        },
        {
            "name": "Google Pixel 7",
            "device_settings": {
                "app_version": "271.0.0.20.110",
                "android_version": "33",
                "android_release": "13",
                "dpi": "420dpi",
                "resolution": "1080x2400",
                "manufacturer": "Google",
                "model": "Pixel 7",
                "device": "cheetah",
                "cpu": "arm64-v8a"
            }
        }
    ]
    with open(DEVICES_FILE, "w") as f:
        json.dump(default_devices, f, indent=4)

# Carregar dispositivos
with open(DEVICES_FILE, "r") as f:
    DEVICES = json.load(f)

# --- Instância do Flask ---
app = Flask(__name__)
# Mantenho a secret_key gerada via env, ou um valor padrão para não quebrar.
# Se você tiver uma secret_key no seu original, pode colocar aqui.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma_chave_secreta_padrao_para_desenvolvimento")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # Tempo de vida da sessão

# --- Funções Auxiliares ---
def save_session(cl, username):
    session_path = os.path.join(SESSION_FOLDER, f"{username}.json")
    try:
        cl.dump_settings(session_path)
        print(f"Sessão salva para {username} em {session_path}")
    except Exception as e:
        print(f"Erro ao salvar a sessão para {username}: {e}")

def load_session(username):
    session_path = os.path.join(SESSION_FOLDER, f"{username}.json")
    if os.path.exists(session_path):
        try:
            cl = Client()
            cl.load_settings(session_path)
            # Mantendo o proxy da variável de ambiente, se você tiver um.
            # Se não tiver, ele será None e não fará nada.
            cl.set_proxy(os.getenv("PROXY", None))
            print(f"Sessão carregada para {username} de {session_path}")
            return cl
        except Exception as e:
            print(f"Erro ao carregar a sessão para {username}: {e}")
            return None
    return None

def write_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_json_file(filename, default_value=None):
    if not os.path.exists(filename):
        return default_value if default_value is not None else {}
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_session_info(username):
    session_path = os.path.join(SESSION_FOLDER, f"{username}.json")
    if os.path.exists(session_path):
        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
                return {
                    "username": username,
                    "proxy": data.get("proxy", "N/A"),
                    "created_at": datetime.fromtimestamp(os.path.getctime(session_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(session_path)).strftime('%Y-%m-%d %H:%M:%S')
                }
        except Exception as e:
            print(f"Erro ao ler informações da sessão para {username}: {e}")
            return None
    return None

def get_all_session_info():
    session_files = [f for f in os.listdir(SESSION_FOLDER) if f.endswith(".json")]
    all_sessions_info = []
    for sf in session_files:
        username = os.path.splitext(sf)[0]
        info = get_session_info(username)
        if info:
            all_sessions_info.append(info)
    return all_sessions_info

def get_account_status(cl):
    try:
        user_info = cl.current_user()
        return "online" if user_info else "offline"
    except Exception:
        return "offline"

# --- Rotas ---

# Rota para o painel de login do administrador
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Usa check_password_hash para comparar a senha fornecida com o hash da senha fixa
        # Para manter compatibilidade exata com o seu código, não geramos hash em tempo real
        # se ADMIN_PASSWORD já for o texto puro.
        # No entanto, a forma mais segura seria ter ADMIN_PASSWORD já como um hash.
        # Como solicitado, mantive a verificação simples.
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Login de administrador bem-sucedido!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
            return redirect(url_for('admin_login'))
    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login de Administrador</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .flash-message {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-danger {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Login de Administrador</h2>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="mb-4">
                        {% for category, message in messages %}
                            <li class="flash-message flash-{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}
            <form action="{{ url_for('admin_login') }}" method="POST" class="space-y-4">
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-700">Usuário</label>
                    <input type="text" id="username" name="username" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700">Senha</label>
                    <input type="password" id="password" name="password" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Login
                    </button>
                </div>
            </form>
        </div>
    </body>
    </html>
    ''')

# Rota para o painel de administrador
@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Você precisa fazer login como administrador para acessar esta página.', 'danger')
        return redirect(url_for('admin_login'))

    all_sessions = get_all_session_info()
    accounts_status = []
    for sess_info in all_sessions:
        cl = load_session(sess_info['username'])
        status = get_account_status(cl) if cl else "offline"
        accounts_status.append({"username": sess_info['username'], "status": status})

    # Carregar todos os pedidos
    orders = read_json_file(os.path.join(ORDERS_FOLDER, "all_orders.json"), [])

    # Carregar todos os grupos
    groups = read_json_file(os.path.join(GROUPS_FOLDER, "groups.json"), {})

    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel de Administrador</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .flash-message {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-danger {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-7xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h2 class="text-3xl font-bold text-center text-gray-800 mb-8">Painel de Administrador</h2>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="mb-4">
                        {% for category, message in messages %}
                            <li class="flash-message flash-{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}

            <div class="mb-8">
                <a href="{{ url_for('admin_logout') }}" class="inline-block bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">Sair</a>
                <a href="{{ url_for('admin_add_device') }}" class="inline-block bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ml-4">Adicionar Dispositivo</a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <h3 class="text-2xl font-semibold text-gray-700 mb-4">Contas Ativas</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuário</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for account in accounts_status %}
                                <tr class="{% if loop.index % 2 == 0 %}bg-gray-50{% else %}bg-white{% endif %}">
                                    <td class="py-2 px-4 border-b">{{ account.username }}</td>
                                    <td class="py-2 px-4 border-b">
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                                                     {% if account.status == 'online' %}bg-green-100 text-green-800{% else %}bg-red-100 text-red-800{% endif %}">
                                            {{ account.status }}
                                        </span>
                                    </td>
                                    <td class="py-2 px-4 border-b">
                                        <form action="{{ url_for('admin_delete_account', username=account.username) }}" method="POST" onsubmit="return confirm('Tem certeza que deseja deletar esta conta?');" class="inline">
                                            <button type="submit" class="text-red-600 hover:text-red-900 text-sm">Deletar</button>
                                        </form>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div>
                    <h3 class="text-2xl font-semibold text-gray-700 mb-4">Gerenciamento de Pedidos</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID do Pedido</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Link</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qtd.</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for order in orders %}
                                <tr class="{% if loop.index % 2 == 0 %}bg-gray-50{% else %}bg-white{% endif %}">
                                    <td class="py-2 px-4 border-b">{{ order.order_id }}</td>
                                    <td class="py-2 px-4 border-b">
                                        <a href="{{ order.link }}" target="_blank" class="text-blue-600 hover:underline">{{ order.link[:30] }}...</a>
                                    </td>
                                    <td class="py-2 px-4 border-b">{{ order.service_type }}</td>
                                    <td class="py-2 px-4 border-b">{{ order.quantity }}</td>
                                    <td class="py-2 px-4 border-b">
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                                                     {% if order.status == 'Concluído' %}bg-green-100 text-green-800
                                                     {% elif order.status == 'Processando' %}bg-yellow-100 text-yellow-800
                                                     {% else %}bg-red-100 text-red-800{% endif %}">
                                            {{ order.status }}
                                        </span>
                                    </td>
                                    <td class="py-2 px-4 border-b">
                                        <form action="{{ url_for('admin_update_order_status', order_id=order.order_id) }}" method="POST" class="inline">
                                            <select name="new_status" class="border border-gray-300 rounded-md py-1 px-2 text-sm">
                                                <option value="Processando" {% if order.status == 'Processando' %}selected{% endif %}>Processando</option>
                                                <option value="Concluído" {% if order.status == 'Concluído' %}selected{% endif %}>Concluído</option>
                                                <option value="Cancelado" {% if order.status == 'Cancelado' %}selected{% endif %}>Cancelado</option>
                                            </select>
                                            <button type="submit" class="ml-2 bg-blue-500 hover:bg-blue-700 text-white text-sm py-1 px-2 rounded">Atualizar</button>
                                        </form>
                                        <form action="{{ url_for('admin_delete_order', order_id=order.order_id) }}" method="POST" onsubmit="return confirm('Tem certeza que deseja deletar este pedido?');" class="inline ml-2">
                                            <button type="submit" class="text-red-600 hover:text-red-900 text-sm">Deletar</button>
                                        </form>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="6" class="py-4 text-center text-gray-500">Nenhum pedido encontrado.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div>
                    <h3 class="text-2xl font-semibold text-gray-700 mb-4">Gerenciamento de Grupos</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome do Grupo</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contas</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for group_name, group_accounts in groups.items() %}
                                <tr class="{% if loop.index % 2 == 0 %}bg-gray-50{% else %}bg-white{% endif %}">
                                    <td class="py-2 px-4 border-b">{{ group_name }}</td>
                                    <td class="py-2 px-4 border-b">
                                        {% if group_accounts %}
                                            <ul class="list-disc list-inside text-sm text-gray-600">
                                                {% for account in group_accounts %}
                                                    <li>{{ account }}</li>
                                                {% endfor %}
                                            </ul>
                                        {% else %}
                                            Nenhuma conta
                                        {% endif %}
                                    </td>
                                    <td class="py-2 px-4 border-b">
                                        <a href="{{ url_for('admin_edit_group', group_name=group_name) }}" class="text-blue-600 hover:text-blue-900 text-sm">Editar</a>
                                        <form action="{{ url_for('admin_delete_group', group_name=group_name) }}" method="POST" onsubmit="return confirm('Tem certeza que deseja deletar este grupo?');" class="inline ml-2">
                                            <button type="submit" class="text-red-600 hover:text-red-900 text-sm">Deletar</button>
                                        </form>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    <div class="mt-4">
                        <h4 class="text-xl font-semibold text-gray-700 mb-2">Adicionar/Editar Grupo</h4>
                        <form action="{{ url_for('admin_add_group') }}" method="POST" class="space-y-4">
                            <div>
                                <label for="group_name" class="block text-sm font-medium text-gray-700">Nome do Grupo</label>
                                <input type="text" id="group_name" name="group_name" required
                                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label for="accounts" class="block text-sm font-medium text-gray-700">Contas (separadas por vírgula)</label>
                                <input type="text" id="accounts" name="accounts"
                                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                       placeholder="conta1,conta2,conta3">
                            </div>
                            <div>
                                <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                                    Adicionar/Atualizar Grupo
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <div>
                    <h3 class="text-2xl font-semibold text-gray-700 mb-4">Dispositivos Cadastrados</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                                    <th class="py-2 px-4 border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for device in DEVICES %}
                                <tr class="{% if loop.index % 2 == 0 %}bg-gray-50{% else %}bg-white{% endif %}">
                                    <td class="py-2 px-4 border-b">{{ device.name }}</td>
                                    <td class="py-2 px-4 border-b">
                                        <form action="{{ url_for('admin_delete_device', device_name=device.name) }}" method="POST" onsubmit="return confirm('Tem certeza que deseja deletar este dispositivo?');" class="inline">
                                            <button type="submit" class="text-red-600 hover:text-red-900 text-sm">Deletar</button>
                                        </form>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Você saiu do painel de administrador.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/delete_account/<username>', methods=['POST'])
def admin_delete_account(username):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    session_path = os.path.join(SESSION_FOLDER, f"{username}.json")
    if os.path.exists(session_path):
        os.remove(session_path)
        flash(f'Conta {username} deletada com sucesso.', 'success')
    else:
        flash(f'Conta {username} não encontrada.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_order_status/<order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    new_status = request.form.get('new_status')
    orders_file = os.path.join(ORDERS_FOLDER, "all_orders.json")
    orders = read_json_file(orders_file, [])

    found = False
    for order in orders:
        if order.get("order_id") == order_id:
            order["status"] = new_status
            found = True
            break
    
    if found:
        write_json_file(orders_file, orders)
        flash(f'Status do pedido {order_id} atualizado para "{new_status}".', 'success')
    else:
        flash(f'Pedido {order_id} não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_order/<order_id>', methods=['POST'])
def admin_delete_order(order_id):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    orders_file = os.path.join(ORDERS_FOLDER, "all_orders.json")
    orders = read_json_file(orders_file, [])

    initial_len = len(orders)
    orders = [order for order in orders if order.get("order_id") != order_id]

    if len(orders) < initial_len:
        write_json_file(orders_file, orders)
        flash(f'Pedido {order_id} deletado com sucesso.', 'success')
    else:
        flash(f'Pedido {order_id} não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_group', methods=['POST'])
def admin_add_group():
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    group_name = request.form.get('group_name')
    accounts_str = request.form.get('accounts', '')
    accounts = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]

    groups_file = os.path.join(GROUPS_FOLDER, "groups.json")
    groups = read_json_file(groups_file, {})

    if not group_name:
        flash('O nome do grupo não pode ser vazio.', 'danger')
    elif group_name in groups and not accounts:
        # Se o grupo já existe e não foram fornecidas contas, é uma tentativa de adicionar um grupo vazio existente
        flash(f'Grupo "{group_name}" já existe. Para atualizar, forneça contas.', 'warning')
    else:
        groups[group_name] = accounts
        write_json_file(groups_file, groups)
        flash(f'Grupo "{group_name}" {"atualizado" if group_name in groups else "adicionado"} com sucesso.', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_group/<group_name>', methods=['GET'])
def admin_edit_group(group_name):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    groups_file = os.path.join(GROUPS_FOLDER, "groups.json")
    groups = read_json_file(groups_file, {})
    group_accounts = groups.get(group_name, [])

    accounts_str = ", ".join(group_accounts)

    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Grupo - {{ group_name }}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .flash-message {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-danger {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Editar Grupo: {{ group_name }}</h2>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="mb-4">
                        {% for category, message in messages %}
                            <li class="flash-message flash-{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}
            <form action="{{ url_for('admin_update_group', group_name=group_name) }}" method="POST" class="space-y-4">
                <div>
                    <label for="accounts" class="block text-sm font-medium text-gray-700">Contas (separadas por vírgula)</label>
                    <input type="text" id="accounts" name="accounts" value="{{ accounts_str }}"
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                           placeholder="conta1,conta2,conta3">
                </div>
                <div>
                    <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Atualizar Grupo
                    </button>
                </div>
            </form>
            <div class="mt-4 text-center">
                <a href="{{ url_for('admin_dashboard') }}" class="text-blue-600 hover:underline">Voltar ao Painel</a>
            </div>
        </div>
    </body>
    </html>
    ''', group_name=group_name, accounts_str=accounts_str)


@app.route('/admin/update_group/<group_name>', methods=['POST'])
def admin_update_group(group_name):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    accounts_str = request.form.get('accounts', '')
    accounts = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]

    groups_file = os.path.join(GROUPS_FOLDER, "groups.json")
    groups = read_json_file(groups_file, {})

    if group_name in groups:
        groups[group_name] = accounts
        write_json_file(groups_file, groups)
        flash(f'Grupo "{group_name}" atualizado com sucesso.', 'success')
    else:
        flash(f'Grupo "{group_name}" não encontrado.', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_group/<group_name>', methods=['POST'])
def admin_delete_group(group_name):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    groups_file = os.path.join(GROUPS_FOLDER, "groups.json")
    groups = read_json_file(groups_file, {})

    if group_name in groups:
        del groups[group_name]
        write_json_file(groups_file, groups)
        flash(f'Grupo "{group_name}" deletado com sucesso.', 'success')
    else:
        flash(f'Grupo "{group_name}" não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_device', methods=['GET', 'POST'])
def admin_add_device():
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        app_version = request.form.get('app_version')
        android_version = request.form.get('android_version')
        android_release = request.form.get('android_release')
        dpi = request.form.get('dpi')
        resolution = request.form.get('resolution')
        manufacturer = request.form.get('manufacturer')
        model = request.form.get('model')
        device = request.form.get('device')
        cpu = request.form.get('cpu')

        if not all([name, app_version, android_version, android_release, dpi, resolution, manufacturer, model, device, cpu]):
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('admin_add_device'))

        new_device = {
            "name": name,
            "device_settings": {
                "app_version": app_version,
                "android_version": android_version,
                "android_release": android_release,
                "dpi": dpi,
                "resolution": resolution,
                "manufacturer": manufacturer,
                "model": model,
                "device": device,
                "cpu": cpu
            }
        }

        # Carregar dispositivos existentes
        current_devices = read_json_file(DEVICES_FILE, [])
        # Verificar se o nome do dispositivo já existe
        if any(d['name'] == name for d in current_devices):
            flash(f'Um dispositivo com o nome "{name}" já existe. Por favor, use um nome diferente.', 'danger')
            return redirect(url_for('admin_add_device'))

        current_devices.append(new_device)
        write_json_file(DEVICES_FILE, current_devices)
        global DEVICES # Atualiza a variável global
        DEVICES = current_devices
        flash(f'Dispositivo "{name}" adicionado com sucesso.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adicionar Novo Dispositivo</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .flash-message {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-danger {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-lg">
            <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Adicionar Novo Dispositivo</h2>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="mb-4">
                        {% for category, message in messages %}
                            <li class="flash-message flash-{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}
            <form action="{{ url_for('admin_add_device') }}" method="POST" class="space-y-4">
                <div>
                    <label for="name" class="block text-sm font-medium text-gray-700">Nome do Dispositivo</label>
                    <input type="text" id="name" name="name" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="app_version" class="block text-sm font-medium text-gray-700">App Version</label>
                    <input type="text" id="app_version" name="app_version" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="android_version" class="block text-sm font-medium text-gray-700">Android Version</label>
                    <input type="text" id="android_version" name="android_version" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="android_release" class="block text-sm font-medium text-gray-700">Android Release</label>
                    <input type="text" id="android_release" name="android_release" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="dpi" class="block text-sm font-medium text-gray-700">DPI</label>
                    <input type="text" id="dpi" name="dpi" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="resolution" class="block text-sm font-medium text-gray-700">Resolution</label>
                    <input type="text" id="resolution" name="resolution" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="manufacturer" class="block text-sm font-medium text-gray-700">Manufacturer</label>
                    <input type="text" id="manufacturer" name="manufacturer" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="model" class="block text-sm font-medium text-gray-700">Model</label>
                    <input type="text" id="model" name="model" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="device" class="block text-sm font-medium text-gray-700">Device</label>
                    <input type="text" id="device" name="device" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="cpu" class="block text-sm font-medium text-gray-700">CPU</label>
                    <input type="text" id="cpu" name="cpu" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Adicionar Dispositivo
                    </button>
                </div>
            </form>
            <div class="mt-4 text-center">
                <a href="{{ url_for('admin_dashboard') }}" class="text-blue-600 hover:underline">Voltar ao Painel</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/delete_device/<device_name>', methods=['POST'])
def admin_delete_device(device_name):
    if not session.get('admin_logged_in'):
        flash('Não autorizado.', 'danger')
        return redirect(url_for('admin_login'))

    current_devices = read_json_file(DEVICES_FILE, [])
    initial_len = len(current_devices)
    updated_devices = [d for d in current_devices if d['name'] != device_name]

    if len(updated_devices) < initial_len:
        write_json_file(DEVICES_FILE, updated_devices)
        global DEVICES # Atualiza a variável global
        DEVICES = updated_devices
        flash(f'Dispositivo "{device_name}" deletado com sucesso.', 'success')
    else:
        flash(f'Dispositivo "{device_name}" não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

# Rota principal para o cliente
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Validar API Key
        api_key_input = request.form.get('api_key')
        if api_key_input != API_KEY: # A validação permanece a mesma com a chave fixa
            flash('Chave de API inválida.', 'danger')
            return redirect(url_for('index'))

        session_id = request.form.get('session_id')
        ds_user_id = request.form.get('ds_user_id')
        username = request.form.get('username')
        device_name = request.form.get('device_name')
        group_name_input = request.form.get('group_name', '').strip()

        if not all([session_id, ds_user_id, username, device_name]):
            flash('Todos os campos obrigatórios (Session ID, DS User ID, Nome de Usuário, Dispositivo) devem ser preenchidos.', 'danger')
            return redirect(url_for('index'))

        cl = Client()
        cl.set_proxy(os.getenv("PROXY", None)) # Mantém a opção de proxy via ENV

        # Encontrar as configurações do dispositivo selecionado
        device_settings = next((d['device_settings'] for d in DEVICES if d['name'] == device_name), None)

        if not device_settings:
            flash('Dispositivo selecionado inválido.', 'danger')
            return redirect(url_for('index'))

        cl.set_device(device_settings)

        try:
            cl.load_settings_from_string(json.dumps({
                "sessionid": session_id,
                "ds_user_id": int(ds_user_id) # Certifica-se de que ds_user_id é um inteiro
            }))
            cl.login_by_sessionid(session_id)
            save_session(cl, username)
            flash(f'Login de {username} bem-sucedido!', 'success')

            # Atribuir a conta a um grupo
            groups = read_json_file(os.path.join(GROUPS_FOLDER, "groups.json"), {})
            group_to_assign = group_name_input if group_name_input else "default"

            if group_to_assign not in groups:
                groups[group_to_assign] = []
            
            if username not in groups[group_to_assign]:
                groups[group_to_assign].append(username)
                write_json_file(os.path.join(GROUPS_FOLDER, "groups.json"), groups)
                flash(f'Conta {username} atribuída ao grupo "{group_to_assign}".', 'info')

            return redirect(url_for('index')) # Redirecionar para a página principal após o login
        except Exception as e:
            flash(f'Erro no login: {e}. Certifique-se de que o Session ID e DS User ID são válidos e a conta não está bloqueada.', 'danger')
            return redirect(url_for('index'))

    # Rota GET - Renderiza o formulário
    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login de Sessão do Instagram</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .flash-message {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-danger {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .flash-info {
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
        </style>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Login de Sessão do Instagram</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="mb-4">
                        {% for category, message in messages %}
                            <li class="flash-message flash-{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}

            <form action="{{ url_for('index') }}" method="POST" class="space-y-4">
                <div>
                    <label for="api_key" class="block text-sm font-medium text-gray-700">Chave de API (22 dígitos)</label>
                    <input type="text" id="api_key" name="api_key" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="session_id" class="block text-sm font-medium text-gray-700">Session ID</label>
                    <input type="text" id="session_id" name="session_id" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="ds_user_id" class="block text-sm font-medium text-gray-700">DS User ID</label>
                    <input type="text" id="ds_user_id" name="ds_user_id" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-700">Nome de Usuário (Instagram)</label>
                    <input type="text" id="username" name="username" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="device_name" class="block text-sm font-medium text-gray-700">Dispositivo</label>
                    <select id="device_name" name="device_name" required
                            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        {% for device in DEVICES %}
                            <option value="{{ device.name }}">{{ device.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="group_name" class="block text-sm font-medium text-gray-700">Nome do Grupo (opcional)</label>
                    <input type="text" id="group_name" name="group_name"
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                    <p class="mt-1 text-xs text-gray-500">Deixe em branco para usar o grupo padrão</p>
                </div>
                
                <div>
                    <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Login
                    </button>
                </div>
            </form>
            
            <div class="mt-6 border-t border-gray-200 pt-4">
                <p class="text-sm text-gray-600">Para obter seu Session ID e DS User ID:</p>
                <ol class="list-decimal list-inside text-sm text-gray-600 mt-2 space-y-1">
                    <li>Acesse o Instagram no navegador</li>
                    <li>Abra as Ferramentas do Desenvolvedor (F12)</li>
                    <li>Vá para a aba Application > Cookies</li>
                    <li>Copie os valores de "sessionid" e "ds_user_id"</li>
                </ol>
            </div>
            <div class="mt-4 text-center">
                <a href="{{ url_for('admin_login') }}" class="text-blue-600 hover:underline text-sm">Acessar Painel de Administrador</a>
            </div>
        </div>
    </body>
    </html>
    ''')

# =========================================================================================================
# Rotas para interações com o Instagram (LIKES, COMMENTS, FOLLOWS) - Podem ser chamadas via API ou outros meios
# =========================================================================================================

@app.route('/api/process_order', methods=['POST'])
def process_order():
    api_key_input = request.headers.get('X-API-KEY')
    if api_key_input != API_KEY: # Validação com a chave fixa
        return jsonify({"status": "error", "message": "API Key inválida."}), 401

    data = request.json
    link = data.get('link')
    service_type = data.get('service_type') # 'likes', 'comments', 'follows'
    quantity = int(data.get('quantity', 1))
    group_name = data.get('group_name', 'default') # Grupo de contas a serem usadas

    if not all([link, service_type, quantity]):
        return jsonify({"status": "error", "message": "Campos 'link', 'service_type' e 'quantity' são obrigatórios."}), 400

    if service_type not in ['likes', 'comments', 'follows', 'views']:
        return jsonify({"status": "error", "message": "Tipo de serviço inválido. Use 'likes', 'comments', 'follows' ou 'views'."}), 400

    order_id = str(random.randint(100000, 999999)) # ID simples para o pedido
    
    # Carregar contas do grupo
    groups = read_json_file(os.path.join(GROUPS_FOLDER, "groups.json"), {})
    accounts_in_group = groups.get(group_name, [])
    
    if not accounts_in_group:
        return jsonify({"status": "error", "message": f"Nenhuma conta encontrada para o grupo '{group_name}'."}), 404

    successful_accounts = []
    failed_accounts = []

    # Registrar o pedido imediatamente
    orders_file = os.path.join(ORDERS_FOLDER, "all_orders.json")
    all_orders = read_json_file(orders_file, [])
    all_orders.append({
        "order_id": order_id,
        "link": link,
        "service_type": service_type,
        "quantity": quantity,
        "group": group_name,
        "status": "Processando", # Inicialmente processando
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    write_json_file(orders_file, all_orders)


    # Lógica de processamento assíncrona ou em thread seria ideal aqui para não bloquear o servidor
    # Por simplicidade, farei de forma síncrona, mas isso deve ser evitado em produção para tarefas longas.
    
    # Criar uma lista de contas com seus objetos CL para não carregar a sessão múltiplas vezes
    active_clients = []
    for account_username in accounts_in_group:
        cl = load_session(account_username)
        if cl and get_account_status(cl) == "online":
            active_clients.append({"username": account_username, "cl": cl})
        else:
            print(f"Conta {account_username} está offline ou não pôde ser carregada, pulando.")
            failed_accounts.append(account_username)

    if not active_clients:
        # Atualizar o status do pedido para 'Falha' se não houver contas ativas
        for order in all_orders:
            if order.get("order_id") == order_id:
                order["status"] = "Falha - Sem contas ativas"
                break
        write_json_file(orders_file, all_orders)
        return jsonify({"status": "error", "message": "Nenhuma conta ativa disponível para processar o pedido.", "failed_accounts": failed_accounts}), 400

    try:
        # Obter media_id se for um link de post/reel
        media_id = None
        user_id = None # Para followers
        if "instagram.com/p/" in link or "instagram.com/reel/" in link:
            # Tentar obter media_id com a primeira conta ativa
            try:
                media_pk = active_clients[0]['cl'].media_pk_from_url(link)
                media_info = active_clients[0]['cl'].media_info(media_pk)
                media_id = media_info.id
            except Exception as e:
                print(f"Erro ao obter media_id: {e}")
                for order in all_orders:
                    if order.get("order_id") == order_id:
                        order["status"] = "Falha - Link inválido ou inacessível"
                        break
                write_json_file(orders_file, all_orders)
                return jsonify({"status": "error", "message": f"Não foi possível obter informações da mídia para o link fornecido. Verifique o link. Erro: {e}"}), 400
        elif "instagram.com/" in link and "/followers" not in link: # Assume que é um perfil para seguir
            try:
                # Extrair username do link (ex: instagram.com/username/)
                profile_username = link.strip('/').split('/')[-1]
                user_info = active_clients[0]['cl'].user_info_by_username(profile_username)
                user_id = user_info.pk
            except Exception as e:
                print(f"Erro ao obter user_id do perfil: {e}")
                for order in all_orders:
                    if order.get("order_id") == order_id:
                        order["status"] = "Falha - Perfil inválido ou inacessível"
                        break
                write_json_file(orders_file, all_orders)
                return jsonify({"status": "error", "message": f"Não foi possível obter informações do perfil para seguir. Verifique o link. Erro: {e}"}), 400


        num_actions_performed = 0
        accounts_to_use = random.sample(active_clients, min(quantity, len(active_clients)))
        
        for account in accounts_to_use:
            cl_account = account['cl']
            username_account = account['username']
            try:
                if service_type == 'likes' and media_id:
                    cl_account.media_like(media_id)
                    num_actions_performed += 1
                    successful_accounts.append(username_account)
                    print(f"Conta {username_account} deu like no post {media_id}")
                elif service_type == 'comments' and media_id:
                    comment = random.choice(EMOJI_COMMENTS)
                    cl_account.media_comment(media_id, comment)
                    num_actions_performed += 1
                    successful_accounts.append(username_account)
                    print(f"Conta {username_account} comentou '{comment}' no post {media_id}")
                elif service_type == 'follows' and user_id:
                    cl_account.user_follow(user_id)
                    num_actions_performed += 1
                    successful_accounts.append(username_account)
                    print(f"Conta {username_account} seguiu o usuário {user_id}")
                elif service_type == 'views' and media_id:
                    cl_account.media_info(media_id) # A simples chamada de media_info registra uma visualização
                    num_actions_performed += 1
                    successful_accounts.append(username_account)
                    print(f"Conta {username_account} visualizou a mídia {media_id}")
                else:
                    raise ValueError("Tipo de serviço ou link incompatível.")
            except Exception as e:
                print(f"Erro na conta {username_account} ao processar {service_type}: {e}")
                failed_accounts.append(username_account)
            time.sleep(random.uniform(2, 5)) # Pequeno delay entre as ações

        # Atualizar o status do pedido com base no resultado
        for order in all_orders:
            if order.get("order_id") == order_id:
                if num_actions_performed >= quantity:
                    order["status"] = "Concluído"
                elif num_actions_performed > 0:
                    order["status"] = f"Parcialmente Concluído ({num_actions_performed}/{quantity})"
                else:
                    order["status"] = "Falha"
                break
        write_json_file(orders_file, all_orders)

        return jsonify({
            "status": "success",
            "order_id": order_id,
            "message": f"Pedido de {service_type} processado. Ações realizadas: {num_actions_performed}.",
            "successful_accounts": successful_accounts,
            "failed_accounts": failed_accounts
        }), 200

    except Exception as e:
        # Em caso de erro geral, atualizar o status do pedido para falha
        for order in all_orders:
            if order.get("order_id") == order_id:
                order["status"] = "Falha - Erro interno"
                break
        write_json_file(orders_file, all_orders)
        return jsonify({"status": "error", "message": f"Ocorreu um erro ao processar o pedido: {e}"}), 500

# Endpoint para listar pedidos (API para uso externo ou cliente)
@app.route('/api/orders', methods=['GET'])
def get_orders():
    api_key_input = request.headers.get('X-API-KEY')
    if api_key_input != API_KEY:
        return jsonify({"status": "error", "message": "API Key inválida."}), 401

    orders_file = os.path.join(ORDERS_FOLDER, "all_orders.json")
    orders = read_json_file(orders_file, [])
    return jsonify(orders), 200

# =============================================

# Iniciar o servidor Flask
if __name__ == '__main__':
    # Esta é a única modificação essencial para o Render:
    # Ele pega a porta da variável de ambiente "PORT" definida pelo Render, ou usa 5000 por padrão.
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() == 'true')