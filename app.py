import os
import json
import time
import random
from datetime import datetime, timedelta
from instagrapi import Client
from flask import Flask, request, render_template_string, redirect, url_for, jsonify, session, flash

# Configurações
SESSION_FOLDER = "sessions"
ORDERS_FOLDER = "orders"
API_KEY = "96b16ebae1c61067bb25fe62"  # Chave de API de 22 dígitos
EMOJI_COMMENTS = ["👍", "❤️", "🔥", "👏", "😎", "🎉", "😍", "🙌", "🤩", "✨"]
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Em produção, use uma senha forte e hash

# Criar pastas se não existirem
if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)
if not os.path.exists(ORDERS_FOLDER):
    os.makedirs(ORDERS_FOLDER)

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_aqui'

# ==============================================
# Funções auxiliares
# ==============================================

def generate_token():
    return ''.join(random.choices('0123456789abcdef', k=22))

def save_session(sessionid, ds_user_id):
    try:
        cl = Client()
        settings = {
            "authorization_data": {"ds_user_id": ds_user_id, "sessionid": sessionid},
            "user_agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T Dev; devitron; qcom; en_US; 314665256)",
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "OnePlus",
                "device": "devitron",
                "model": "6T Dev",
                "cpu": "qcom",
                "version_code": "314665256"
            }
        }
        cl.set_settings(settings)
        info = cl.account_info()
        username = info.username
        session_file = os.path.join(SESSION_FOLDER, f"{username}_session.json")
        cl.dump_settings(session_file)
        print(f"✅ Login bem-sucedido para @{username}")
        return True, username
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {str(e)}"
        print(f"❌ Erro ao validar sessão: {error_message}")
        return False, error_message

def comment_post(client, post_url, comment):
    try:
        media_id = client.media_pk_from_url(post_url)
        if not media_id:
            print(f"Erro: Não foi possível obter o ID da mídia para {post_url}.")
            return False, "Não foi possível obter o ID da mídia."
        client.media_comment(media_id, comment)
        print(f"Comentário enviado: {comment}")
        return True, ""
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {str(e)}"
        print(f"Erro ao comentar na publicação {post_url}: {error_message}")
        return False, error_message

def validate_api_key(key):
    return key == API_KEY and len(key) == 22

def get_next_order_id():
    order_files = [f for f in os.listdir(ORDERS_FOLDER) if f.startswith("order_") and f.endswith(".json")]
    if not order_files:
        return 1
    max_id = max(int(f.split("_")[1].split(".")[0]) for f in order_files)
    return max_id + 1

def create_order(link, quantity, username):
    order_id = get_next_order_id()
    order = {
        "id": order_id,
        "user": username,
        "charge": round(random.uniform(0.1, 0.3), 3),
        "link": link,
        "start_count": 312,
        "quantity": quantity,
        "service": "Instagram Likes Organic Premium | Brazil ★ R30 | Max 6K | Start: 15m",
        "status": "pending",
        "remains": None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "Auto"
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

# ==============================================
# Rotas de Autenticação
# ==============================================

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
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100 h-screen flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h1 class="text-2xl font-bold text-center mb-6 text-gray-800">Painel Administrativo</h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="mb-4 p-3 rounded text-white bg-red-500">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" class="space-y-4">
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
                    <button type="submit" 
                            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Entrar
                    </button>
                </div>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ==============================================
# Painel Administrativo
# ==============================================

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    period = request.args.get('period', 'daily')
    search_query = request.args.get('search', '')
    
    stats = get_stats(period)
    orders = list_orders(search_query)
    logged_accounts = len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')])
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100">
        <!-- Sidebar -->
        <div class="flex h-screen">
            <div class="bg-indigo-800 text-white w-64 space-y-6 py-7 px-2 fixed inset-y-0 left-0 transform -translate-x-full md:translate-x-0 transition duration-200 ease-in-out">
                <div class="text-white flex items-center space-x-2 px-4">
                    <i class="fas fa-robot text-2xl"></i>
                    <span class="text-xl font-bold">Instagram Bot</span>
                </div>
                
                <nav>
                    <a href="{{ url_for('admin_dashboard') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                    </a>
                    
                    <a href="{{ url_for('admin_orders') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-list-alt mr-2"></i>Pedidos
                    </a>
                    
                    <a href="{{ url_for('admin_accounts') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-users mr-2"></i>Contas ({{ logged_accounts }})
                    </a>
                    
                    <a href="{{ url_for('admin_send') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-paper-plane mr-2"></i>Enviar Comentários
                    </a>
                    
                    <a href="{{ url_for('admin_settings') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-cog mr-2"></i>Configurações
                    </a>
                    
                    <a href="{{ url_for('admin_logout') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-sign-out-alt mr-2"></i>Sair
                    </a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 md:ml-64">
                <!-- Top Navigation -->
                <header class="bg-white shadow-sm">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-tachometer-alt mr-2"></i> Dashboard
                        </h1>
                        <div class="text-sm text-gray-500">
                            <i class="fas fa-calendar-alt mr-1"></i> {{ datetime.now().strftime("%d/%m/%Y %H:%M") }}
                        </div>
                    </div>
                </header>
                
                <!-- Stats Cards -->
                <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <div class="px-4 py-6 sm:px-0">
                        <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                            <!-- Total Orders -->
                            <div class="bg-white overflow-hidden shadow rounded-lg">
                                <div class="px-4 py-5 sm:p-6">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                                            <i class="fas fa-shopping-cart text-white"></i>
                                        </div>
                                        <div class="ml-5 w-0 flex-1">
                                            <dl>
                                                <dt class="text-sm font-medium text-gray-500 truncate">Pedidos Totais</dt>
                                                <dd class="flex items-baseline">
                                                    <div class="text-2xl font-semibold text-gray-900">{{ stats.total }}</div>
                                                </dd>
                                            </dl>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Completed Orders -->
                            <div class="bg-white overflow-hidden shadow rounded-lg">
                                <div class="px-4 py-5 sm:p-6">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0 bg-green-500 rounded-md p-3">
                                            <i class="fas fa-check-circle text-white"></i>
                                        </div>
                                        <div class="ml-5 w-0 flex-1">
                                            <dl>
                                                <dt class="text-sm font-medium text-gray-500 truncate">Concluídos</dt>
                                                <dd class="flex items-baseline">
                                                    <div class="text-2xl font-semibold text-gray-900">{{ stats.completed }}</div>
                                                </dd>
                                            </dl>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Pending Orders -->
                            <div class="bg-white overflow-hidden shadow rounded-lg">
                                <div class="px-4 py-5 sm:p-6">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                                            <i class="fas fa-clock text-white"></i>
                                        </div>
                                        <div class="ml-5 w-0 flex-1">
                                            <dl>
                                                <dt class="text-sm font-medium text-gray-500 truncate">Pendentes</dt>
                                                <dd class="flex items-baseline">
                                                    <div class="text-2xl font-semibold text-gray-900">{{ stats.pending }}</div>
                                                </dd>
                                            </dl>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Charts -->
                        <div class="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-2">
                            <!-- Orders Chart -->
                            <div class="bg-white overflow-hidden shadow rounded-lg">
                                <div class="px-4 py-5 sm:p-6">
                                    <h3 class="text-lg font-medium text-gray-900">Estatísticas de Pedidos</h3>
                                    <div class="mt-4">
                                        <canvas id="ordersChart" height="200"></canvas>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Recent Orders -->
                            <div class="bg-white overflow-hidden shadow rounded-lg">
                                <div class="px-4 py-5 sm:p-6">
                                    <div class="flex justify-between items-center">
                                        <h3 class="text-lg font-medium text-gray-900">Pedidos Recentes</h3>
                                        <a href="{{ url_for('admin_orders') }}" class="text-sm text-indigo-600 hover:text-indigo-900">Ver todos</a>
                                    </div>
                                    <div class="mt-4 flow-root">
                                        <div class="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                                            <div class="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                                                <div class="overflow-hidden border-b border-gray-200">
                                                    <table class="min-w-full divide-y divide-gray-200">
                                                        <thead class="bg-gray-50">
                                                            <tr>
                                                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Link</th>
                                                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody class="bg-white divide-y divide-gray-200">
                                                            {% for order in orders[:5] %}
                                                            <tr>
                                                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{{ order.id }}</td>
                                                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-xs">{{ order.link }}</td>
                                                                <td class="px-6 py-4 whitespace-nowrap">
                                                                    {% if order.status == 'completed' %}
                                                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Concluído</span>
                                                                    {% elif order.status == 'pending' %}
                                                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Pendente</span>
                                                                    {% elif order.status == 'in_progress' %}
                                                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">Em Progresso</span>
                                                                    {% elif order.status == 'canceled' %}
                                                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Cancelado</span>
                                                                    {% else %}
                                                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{{ order.status }}</span>
                                                                    {% endif %}
                                                                </td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
        
        <script>
            // Orders Chart
            const ordersCtx = document.getElementById('ordersChart').getContext('2d');
            const ordersChart = new Chart(ordersCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Concluídos', 'Pendentes', 'Em Progresso', 'Cancelados', 'Parciais'],
                    datasets: [{
                        data: [
                            {{ stats.completed }},
                            {{ stats.pending }},
                            {{ stats.in_progress }},
                            {{ stats.canceled }},
                            {{ stats.partial }}
                        ],
                        backgroundColor: [
                            '#10B981',
                            '#F59E0B',
                            '#3B82F6',
                            '#EF4444',
                            '#8B5CF6'
                        ],
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    ''', stats=stats, orders=orders, logged_accounts=logged_accounts, datetime=datetime)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    search_query = request.args.get('search', '')
    orders = list_orders(search_query)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pedidos - Painel Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <!-- Sidebar -->
        <div class="flex h-screen">
            <div class="bg-indigo-800 text-white w-64 space-y-6 py-7 px-2 fixed inset-y-0 left-0 transform -translate-x-full md:translate-x-0 transition duration-200 ease-in-out">
                <div class="text-white flex items-center space-x-2 px-4">
                    <i class="fas fa-robot text-2xl"></i>
                    <span class="text-xl font-bold">Instagram Bot</span>
                </div>
                
                <nav>
                    <a href="{{ url_for('admin_dashboard') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                    </a>
                    
                    <a href="{{ url_for('admin_orders') }}" class="block py-2.5 px-4 rounded transition duration-200 bg-indigo-700 text-white">
                        <i class="fas fa-list-alt mr-2"></i>Pedidos
                    </a>
                    
                    <a href="{{ url_for('admin_accounts') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-users mr-2"></i>Contas ({{ logged_accounts }})
                    </a>
                    
                    <a href="{{ url_for('admin_send') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-paper-plane mr-2"></i>Enviar Comentários
                    </a>
                    
                    <a href="{{ url_for('admin_settings') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-cog mr-2"></i>Configurações
                    </a>
                    
                    <a href="{{ url_for('admin_logout') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-sign-out-alt mr-2"></i>Sair
                    </a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 md:ml-64">
                <!-- Top Navigation -->
                <header class="bg-white shadow-sm">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-list-alt mr-2"></i> Pedidos
                        </h1>
                        <div class="text-sm text-gray-500">
                            <i class="fas fa-calendar-alt mr-1"></i> {{ datetime.now().strftime("%d/%m/%Y %H:%M") }}
                        </div>
                    </div>
                </header>
                
                <!-- Main Content -->
                <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <div class="px-4 py-6 sm:px-0">
                        <!-- Search and Filters -->
                        <div class="mb-6 bg-white p-4 rounded-lg shadow">
                            <form method="GET" class="flex flex-col md:flex-row gap-4">
                                <div class="flex-1">
                                    <input type="text" name="search" placeholder="Pesquisar por ID, Link ou Status" 
                                           value="{{ search_query }}" class="w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500">
                                </div>
                                <button type="submit" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                                    <i class="fas fa-search mr-2"></i> Pesquisar
                                </button>
                                <a href="{{ url_for('admin_orders') }}" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-center">
                                    <i class="fas fa-sync-alt mr-2"></i> Limpar
                                </a>
                            </form>
                        </div>
                        
                        <!-- Orders Table -->
                        <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                            <div class="overflow-x-auto">
                                <table class="min-w-full divide-y divide-gray-200">
                                    <thead class="bg-gray-50">
                                        <tr>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuário</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Link</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantidade</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Criado em</th>
                                            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white divide-y divide-gray-200">
                                        {% for order in orders %}
                                        <tr>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{{ order.id }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ order.user }}</td>
                                            <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{{ order.link }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ order.quantity }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap">
                                                {% if order.status == 'completed' %}
                                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Concluído</span>
                                                {% elif order.status == 'pending' %}
                                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Pendente</span>
                                                {% elif order.status == 'in_progress' %}
                                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">Em Progresso</span>
                                                {% elif order.status == 'canceled' %}
                                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Cancelado</span>
                                                {% else %}
                                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{{ order.status }}</span>
                                                {% endif %}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ order.created_at }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <a href="#" class="text-indigo-600 hover:text-indigo-900 mr-3"><i class="fas fa-eye"></i></a>
                                                <a href="#" class="text-yellow-600 hover:text-yellow-900"><i class="fas fa-edit"></i></a>
                                            </td>
                                        </tr>
                                        {% else %}
                                        <tr>
                                            <td colspan="7" class="px-6 py-4 text-center text-sm text-gray-500">Nenhum pedido encontrado</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    </body>
    </html>
    ''', orders=orders, search_query=search_query, logged_accounts=len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')]), datetime=datetime)

@app.route('/admin/accounts')
def admin_accounts():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    session_files = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')]
    accounts = []
    
    for session_file in session_files:
        username = session_file.split('_session.json')[0]
        file_path = os.path.join(SESSION_FOLDER, session_file)
        with open(file_path, 'r') as f:
            session_data = json.load(f)
            accounts.append({
                'username': username,
                'ds_user_id': session_data['authorization_data']['ds_user_id'],
                'sessionid': session_data['authorization_data']['sessionid'],
                'last_used': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%d/%m/%Y %H:%M')
            })
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contas - Painel Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <!-- Sidebar -->
        <div class="flex h-screen">
            <div class="bg-indigo-800 text-white w-64 space-y-6 py-7 px-2 fixed inset-y-0 left-0 transform -translate-x-full md:translate-x-0 transition duration-200 ease-in-out">
                <div class="text-white flex items-center space-x-2 px-4">
                    <i class="fas fa-robot text-2xl"></i>
                    <span class="text-xl font-bold">Instagram Bot</span>
                </div>
                
                <nav>
                    <a href="{{ url_for('admin_dashboard') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                    </a>
                    
                    <a href="{{ url_for('admin_orders') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-list-alt mr-2"></i>Pedidos
                    </a>
                    
                    <a href="{{ url_for('admin_accounts') }}" class="block py-2.5 px-4 rounded transition duration-200 bg-indigo-700 text-white">
                        <i class="fas fa-users mr-2"></i>Contas ({{ accounts|length }})
                    </a>
                    
                    <a href="{{ url_for('admin_send') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-paper-plane mr-2"></i>Enviar Comentários
                    </a>
                    
                    <a href="{{ url_for('admin_settings') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-cog mr-2"></i>Configurações
                    </a>
                    
                    <a href="{{ url_for('admin_logout') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-sign-out-alt mr-2"></i>Sair
                    </a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 md:ml-64">
                <!-- Top Navigation -->
                <header class="bg-white shadow-sm">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-users mr-2"></i> Contas Conectadas
                        </h1>
                        <div class="text-sm text-gray-500">
                            <i class="fas fa-calendar-alt mr-1"></i> {{ datetime.now().strftime("%d/%m/%Y %H:%M") }}
                        </div>
                    </div>
                </header>
                
                <!-- Main Content -->
                <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <div class="px-4 py-6 sm:px-0">
                        <!-- Add Account Button -->
                        <div class="mb-6 flex justify-end">
                            <button onclick="document.getElementById('addAccountModal').classList.remove('hidden')" 
                                    class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                                <i class="fas fa-plus mr-2"></i> Adicionar Conta
                            </button>
                        </div>
                        
                        <!-- Accounts Table -->
                        <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                            <div class="overflow-x-auto">
                                <table class="min-w-full divide-y divide-gray-200">
                                    <thead class="bg-gray-50">
                                        <tr>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuário</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DS User ID</th>
                                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Último Uso</th>
                                            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white divide-y divide-gray-200">
                                        {% for account in accounts %}
                                        <tr>
                                            <td class="px-6 py-4 whitespace-nowrap">
                                                <div class="flex items-center">
                                                    <div class="flex-shrink-0 h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                                                        <i class="fas fa-user text-indigo-600"></i>
                                                    </div>
                                                    <div class="ml-4">
                                                        <div class="text-sm font-medium text-gray-900">@{{ account.username }}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ account.ds_user_id }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ account.last_used }}</td>
                                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button onclick="showAccountDetails('{{ account.username }}', '{{ account.ds_user_id }}', '{{ account.sessionid }}')" 
                                                        class="text-indigo-600 hover:text-indigo-900 mr-3">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                                <button onclick="confirmDelete('{{ account.username }}')" 
                                                        class="text-red-600 hover:text-red-900">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </td>
                                        </tr>
                                        {% else %}
                                        <tr>
                                            <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">Nenhuma conta encontrada</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
        
        <!-- Add Account Modal -->
        <div id="addAccountModal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <h3 class="text-lg leading-6 font-medium text-gray-900">Adicionar Nova Conta</h3>
                    <div class="mt-2 px-7 py-3">
                        <form id="addAccountForm" action="{{ url_for('add_account') }}" method="POST">
                            <div class="mb-4">
                                <label for="sessionid" class="block text-sm font-medium text-gray-700 text-left mb-1">Session ID</label>
                                <input type="text" id="sessionid" name="sessionid" required 
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div class="mb-4">
                                <label for="ds_user_id" class="block text-sm font-medium text-gray-700 text-left mb-1">DS User ID</label>
                                <input type="text" id="ds_user_id" name="ds_user_id" required 
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                        </form>
                    </div>
                    <div class="items-center px-4 py-3">
                        <button onclick="document.getElementById('addAccountModal').classList.add('hidden')" 
                                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md mr-2 hover:bg-gray-300">
                            Cancelar
                        </button>
                        <button type="submit" form="addAccountForm" 
                                class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                            Adicionar
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Account Details Modal -->
        <div id="accountDetailsModal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <h3 class="text-lg leading-6 font-medium text-gray-900">Detalhes da Conta</h3>
                    <div class="mt-2 px-7 py-3 text-left">
                        <div class="mb-2">
                            <span class="font-medium">Usuário:</span> <span id="detailUsername"></span>
                        </div>
                        <div class="mb-2">
                            <span class="font-medium">DS User ID:</span> <span id="detailDsUserId"></span>
                        </div>
                        <div class="mb-2">
                            <span class="font-medium">Session ID:</span> 
                            <div class="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto" id="detailSessionId"></div>
                        </div>
                    </div>
                    <div class="items-center px-4 py-3">
                        <button onclick="document.getElementById('accountDetailsModal').classList.add('hidden')" 
                                class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                            Fechar
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Delete Confirmation Modal -->
        <div id="deleteConfirmationModal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                        <i class="fas fa-exclamation text-red-600"></i>
                    </div>
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mt-3">Confirmar Exclusão</h3>
                    <div class="mt-2 px-7 py-3">
                        <p class="text-sm text-gray-500">Tem certeza que deseja remover esta conta? Esta ação não pode ser desfeita.</p>
                    </div>
                    <div class="items-center px-4 py-3">
                        <form id="deleteAccountForm" action="{{ url_for('delete_account') }}" method="POST">
                            <input type="hidden" id="deleteUsername" name="username">
                            <button onclick="document.getElementById('deleteConfirmationModal').classList.add('hidden')" type="button" 
                                    class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md mr-2 hover:bg-gray-300">
                                Cancelar
                            </button>
                            <button type="submit" 
                                    class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                                Excluir
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function showAccountDetails(username, dsUserId, sessionId) {
                document.getElementById('detailUsername').textContent = '@' + username;
                document.getElementById('detailDsUserId').textContent = dsUserId;
                document.getElementById('detailSessionId').textContent = sessionId;
                document.getElementById('accountDetailsModal').classList.remove('hidden');
            }
            
            function confirmDelete(username) {
                document.getElementById('deleteUsername').value = username;
                document.getElementById('deleteConfirmationModal').classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    ''', accounts=accounts, datetime=datetime)

@app.route('/admin/send', methods=['GET', 'POST'])
def admin_send():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    logged_accounts = len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')])
    message = ""
    
    if request.method == 'POST':
        post_url = request.form.get('post_url', '').strip()
        quantity = int(request.form.get('quantity', 1))
        
        if not post_url:
            flash('URL do post é obrigatória', 'error')
        elif logged_accounts == 0:
            flash('Nenhuma conta está logada para enviar comentários.', 'error')
        else:
            order_id = create_order(post_url, quantity, session.get('admin_username', 'admin'))
            comments_sent = 0
            error_logs = []
            update_order(order_id, {"status": "in progress"})
            
            session_files = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')]
            for session_file in session_files:
                if comments_sent >= quantity:
                    break
                
                username = session_file.split("_session.json")[0]
                try:
                    cl = Client()
                    session_path = os.path.join(SESSION_FOLDER, session_file)
                    with open(session_path, 'r') as f:
                        cl.set_settings(json.load(f))
                    cl.account_info()
                    comment = random.choice(EMOJI_COMMENTS)
                    success, error_message = comment_post(cl, post_url, comment)
                    
                    if success:
                        comments_sent += 1
                    else:
                        error_logs.append(f"Erro por {username}: {error_message}")
                    
                    time.sleep(random.uniform(5, 10))
                except Exception as e:
                    error_logs.append(f"Erro com {username}: {str(e)}")
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
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enviar Comentários - Painel Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <!-- Sidebar -->
        <div class="flex h-screen">
            <div class="bg-indigo-800 text-white w-64 space-y-6 py-7 px-2 fixed inset-y-0 left-0 transform -translate-x-full md:translate-x-0 transition duration-200 ease-in-out">
                <div class="text-white flex items-center space-x-2 px-4">
                    <i class="fas fa-robot text-2xl"></i>
                    <span class="text-xl font-bold">Instagram Bot</span>
                </div>
                
                <nav>
                    <a href="{{ url_for('admin_dashboard') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                    </a>
                    
                    <a href="{{ url_for('admin_orders') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-list-alt mr-2"></i>Pedidos
                    </a>
                    
                    <a href="{{ url_for('admin_accounts') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-users mr-2"></i>Contas ({{ logged_accounts }})
                    </a>
                    
                    <a href="{{ url_for('admin_send') }}" class="block py-2.5 px-4 rounded transition duration-200 bg-indigo-700 text-white">
                        <i class="fas fa-paper-plane mr-2"></i>Enviar Comentários
                    </a>
                    
                    <a href="{{ url_for('admin_settings') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-cog mr-2"></i>Configurações
                    </a>
                    
                    <a href="{{ url_for('admin_logout') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-sign-out-alt mr-2"></i>Sair
                    </a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 md:ml-64">
                <!-- Top Navigation -->
                <header class="bg-white shadow-sm">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-paper-plane mr-2"></i> Enviar Comentários
                        </h1>
                        <div class="text-sm text-gray-500">
                            <i class="fas fa-calendar-alt mr-1"></i> {{ datetime.now().strftime("%d/%m/%Y %H:%M") }}
                        </div>
                    </div>
                </header>
                
                <!-- Main Content -->
                <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <div class="px-4 py-6 sm:px-0">
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="mb-4 p-3 rounded text-white 
                                        {% if category == 'error' %}bg-red-500
                                        {% elif category == 'warning' %}bg-yellow-500
                                        {% else %}bg-green-500{% endif %}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <!-- Send Form -->
                        <div class="bg-white p-6 rounded-lg shadow">
                            <form method="POST" class="space-y-4">
                                <div>
                                    <label for="post_url" class="block text-sm font-medium text-gray-700">URL do Post</label>
                                    <input type="text" id="post_url" name="post_url" required 
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" 
                                           placeholder="https://www.instagram.com/p/...">
                                </div>
                                
                                <div>
                                    <label for="quantity" class="block text-sm font-medium text-gray-700">Quantidade de Comentários</label>
                                    <input type="number" id="quantity" name="quantity" min="1" value="1" required 
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                                </div>
                                
                                <div class="pt-4">
                                    <button type="submit" 
                                            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                        <i class="fas fa-paper-plane mr-2"></i> Enviar Comentários
                                    </button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Accounts Info -->
                        <div class="mt-6 bg-white p-6 rounded-lg shadow">
                            <h3 class="text-lg font-medium text-gray-900 mb-4">
                                <i class="fas fa-info-circle mr-2"></i> Informações
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="p-4 border rounded-lg">
                                    <h4 class="font-medium text-gray-700 mb-2">
                                        <i class="fas fa-users mr-2"></i> Contas Disponíveis
                                    </h4>
                                    <p class="text-gray-600">Você tem <span class="font-bold">{{ logged_accounts }}</span> contas conectadas para enviar comentários.</p>
                                </div>
                                <div class="p-4 border rounded-lg">
                                    <h4 class="font-medium text-gray-700 mb-2">
                                        <i class="fas fa-comment mr-2"></i> Comentários Padrão
                                    </h4>
                                    <p class="text-gray-600">Os comentários serão selecionados aleatoriamente desta lista: 
                                        <span class="font-bold">{{ EMOJI_COMMENTS|join(', ') }}</span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    </body>
    </html>
    ''', logged_accounts=logged_accounts, EMOJI_COMMENTS=EMOJI_COMMENTS, datetime=datetime)

@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Configurações - Painel Administrativo</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <!-- Sidebar -->
        <div class="flex h-screen">
            <div class="bg-indigo-800 text-white w-64 space-y-6 py-7 px-2 fixed inset-y-0 left-0 transform -translate-x-full md:translate-x-0 transition duration-200 ease-in-out">
                <div class="text-white flex items-center space-x-2 px-4">
                    <i class="fas fa-robot text-2xl"></i>
                    <span class="text-xl font-bold">Instagram Bot</span>
                </div>
                
                <nav>
                    <a href="{{ url_for('admin_dashboard') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                    </a>
                    
                    <a href="{{ url_for('admin_orders') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-list-alt mr-2"></i>Pedidos
                    </a>
                    
                    <a href="{{ url_for('admin_accounts') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-users mr-2"></i>Contas ({{ logged_accounts }})
                    </a>
                    
                    <a href="{{ url_for('admin_send') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-paper-plane mr-2"></i>Enviar Comentários
                    </a>
                    
                    <a href="{{ url_for('admin_settings') }}" class="block py-2.5 px-4 rounded transition duration-200 bg-indigo-700 text-white">
                        <i class="fas fa-cog mr-2"></i>Configurações
                    </a>
                    
                    <a href="{{ url_for('admin_logout') }}" class="block py-2.5 px-4 rounded transition duration-200 hover:bg-indigo-700 hover:text-white">
                        <i class="fas fa-sign-out-alt mr-2"></i>Sair
                    </a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 md:ml-64">
                <!-- Top Navigation -->
                <header class="bg-white shadow-sm">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-cog mr-2"></i> Configurações
                        </h1>
                        <div class="text-sm text-gray-500">
                            <i class="fas fa-calendar-alt mr-1"></i> {{ datetime.now().strftime("%d/%m/%Y %H:%M") }}
                        </div>
                    </div>
                </header>
                
                <!-- Main Content -->
                <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <div class="px-4 py-6 sm:px-0">
                        <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
                                <h3 class="text-lg leading-6 font-medium text-gray-900">
                                    Configurações do Sistema
                                </h3>
                            </div>
                            <div class="px-4 py-5 sm:p-6">
                                <form class="space-y-6">
                                    <div>
                                        <label for="api_key" class="block text-sm font-medium text-gray-700">Chave da API</label>
                                        <div class="mt-1 flex rounded-md shadow-sm">
                                            <input type="text" id="api_key" readonly value="{{ API_KEY }}" 
                                                   class="flex-1 block w-full rounded-none rounded-l-md border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border py-2 px-3 bg-gray-100">
                                            <button type="button" onclick="copyToClipboard('api_key')" 
                                                    class="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm hover:bg-gray-100">
                                                <i class="fas fa-copy mr-1"></i> Copiar
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label for="emoji_comments" class="block text-sm font-medium text-gray-700">Comentários Padrão</label>
                                        <textarea id="emoji_comments" rows="3" 
                                                  class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border border-gray-300 rounded-md p-2" 
                                                  placeholder="Lista de emojis para comentários">{{ EMOJI_COMMENTS|join(', ') }}</textarea>
                                    </div>
                                    
                                    <div class="pt-4">
                                        <button type="submit" 
                                                class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                            <i class="fas fa-save mr-2"></i> Salvar Configurações
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                        
                        <div class="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
                            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
                                <h3 class="text-lg leading-6 font-medium text-gray-900">
                                    Informações do Sistema
                                </h3>
                            </div>
                            <div class="px-4 py-5 sm:p-6">
                                <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-500">Versão do Sistema</dt>
                                        <dd class="mt-1 text-sm text-gray-900">1.0.0</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-500">Contas Conectadas</dt>
                                        <dd class="mt-1 text-sm text-gray-900">{{ logged_accounts }}</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-500">Pedidos Totais</dt>
                                        <dd class="mt-1 text-sm text-gray-900">{{ total_orders }}</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-500">Última Atualização</dt>
                                        <dd class="mt-1 text-sm text-gray-900">{{ datetime.now().strftime("%d/%m/%Y %H:%M") }}</dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
        
        <script>
            function copyToClipboard(elementId) {
                const element = document.getElementById(elementId);
                element.select();
                element.setSelectionRange(0, 99999);
                document.execCommand("copy");
                
                // Mostrar notificação
                const notification = document.createElement('div');
                notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg';
                notification.textContent = 'Copiado para a área de transferência!';
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.remove();
                }, 2000);
            }
        </script>
    </body>
    </html>
    ''', logged_accounts=len([f for f in os.listdir(SESSION_FOLDER) if f.endswith('_session.json')]), 
         total_orders=len([f for f in os.listdir(ORDERS_FOLDER) if f.startswith('order_') and f.endswith('.json')]), 
         API_KEY=API_KEY, EMOJI_COMMENTS=EMOJI_COMMENTS, datetime=datetime)

# ==============================================
# Rotas para ações administrativas
# ==============================================

@app.route('/admin/add_account', methods=['POST'])
def add_account():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    sessionid = request.form.get('sessionid', '').strip()
    ds_user_id = request.form.get('ds_user_id', '').strip()
    
    if not sessionid or not ds_user_id:
        flash('Ambos sessionid e ds_user_id são obrigatórios.', 'error')
        return redirect(url_for('admin_accounts'))
    
    success, result = save_session(sessionid, ds_user_id)
    if success:
        flash(f'Conta @{result} adicionada com sucesso!', 'success')
    else:
        flash(f'Falha ao adicionar conta: {result}', 'error')
    
    return redirect(url_for('admin_accounts'))

@app.route('/admin/delete_account', methods=['POST'])
def delete_account():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    username = request.form.get('username', '').strip()
    if not username:
        flash('Nome de usuário não especificado.', 'error')
        return redirect(url_for('admin_accounts'))
    
    session_file = os.path.join(SESSION_FOLDER, f"{username}_session.json")
    if os.path.exists(session_file):
        os.remove(session_file)
        flash(f'Conta @{username} removida com sucesso!', 'success')
    else:
        flash(f'Conta @{username} não encontrada.', 'error')
    
    return redirect(url_for('admin_accounts'))

# ==============================================
# API Endpoints
# ==============================================

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
                "service": order["service"],
                "status": order["status"],
                "remains": order["remains"],
                "created_at": order["created_at"],
                "mode": order["mode"]
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
            if status in ['pending', 'in progress', 'processing', 'canceled', 'partial', 'completed']:
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
    
    return jsonify({"status": "error", "error": "Ação inválida"})

# ==============================================
# Rotas Públicas (para login de contas Instagram)
# ==============================================

@app.route('/login', methods=['GET', 'POST'])
def public_login():
    if request.method == 'POST':
        sessionid = request.form.get('sessionid', '').strip()
        ds_user_id = request.form.get('ds_user_id', '').strip()
        
        if not sessionid or not ds_user_id:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login com Session ID</title>
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            </head>
            <body class="bg-gray-100 h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                    <h2 class="text-2xl font-bold text-center mb-6 text-gray-800">Login com Session ID</h2>
                    
                    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
                        <strong class="font-bold">Erro!</strong>
                        <span class="block sm:inline">Ambos sessionid e ds_user_id são obrigatórios.</span>
                    </div>
                    
                    <form method="POST" class="space-y-4">
                        <div>
                            <label for="sessionid" class="block text-sm font-medium text-gray-700">Session ID</label>
                            <input type="text" id="sessionid" name="sessionid" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        </div>
                        
                        <div>
                            <label for="ds_user_id" class="block text-sm font-medium text-gray-700">DS User ID</label>
                            <input type="text" id="ds_user_id" name="ds_user_id" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
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
        
        success, result = save_session(sessionid, ds_user_id)
        if success:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Bem-sucedido</title>
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            </head>
            <body class="bg-gray-100 h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md text-center">
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                        <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-center mb-2 text-gray-800">Login Bem-sucedido!</h2>
                    <p class="text-gray-600 mb-6">Conta @{{ username }} conectada com sucesso.</p>
                    <a href="{{ url_for('admin_dashboard') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Ir para o Painel
                    </a>
                </div>
            </body>
            </html>
            ''', username=result)
        else:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Falha no Login</title>
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            </head>
            <body class="bg-gray-100 h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                    <h2 class="text-2xl font-bold text-center mb-6 text-gray-800">Login com Session ID</h2>
                    
                    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
                        <strong class="font-bold">Erro!</strong>
                        <span class="block sm:inline">Falha no login: {{ error_message }}</span>
                    </div>
                    
                    <form method="POST" class="space-y-4">
                        <div>
                            <label for="sessionid" class="block text-sm font-medium text-gray-700">Session ID</label>
                            <input type="text" id="sessionid" name="sessionid" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        </div>
                        
                        <div>
                            <label for="ds_user_id" class="block text-sm font-medium text-gray-700">DS User ID</label>
                            <input type="text" id="ds_user_id" name="ds_user_id" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        </div>
                        
                        <div>
                            <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Tentar Novamente
                            </button>
                        </div>
                    </form>
                </div>
            </body>
            </html>
            ''', error_message=result)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login com Session ID</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100 h-screen flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h2 class="text-2xl font-bold text-center mb-6 text-gray-800">Login com Session ID</h2>
            
            <form method="POST" class="space-y-4">
                <div>
                    <label for="sessionid" class="block text-sm font-medium text-gray-700">Session ID</label>
                    <input type="text" id="sessionid" name="sessionid" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                
                <div>
                    <label for="ds_user_id" class="block text-sm font-medium text-gray-700">DS User ID</label>
                    <input type="text" id="ds_user_id" name="ds_user_id" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
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
        </div>
    </body>
    </html>
    ''')

# ==============================================
# Inicialização do Servidor
# ==============================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
