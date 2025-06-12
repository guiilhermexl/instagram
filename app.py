import os
import sqlite3
from flask import Flask, request, redirect, url_for, session, flash, get_flashed_messages, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# MUDE ESTA CHAVE SECRETA PARA UMA STRING LONGA E ALEATÓRIA EM UM AMBIENTE DE PRODUÇÃO
app.secret_key = 'sua_chave_secreta_muito_segura_aqui_12345'

# Define a pasta para uploads de vídeos
UPLOAD_FOLDER = 'static/videos'
DATABASE = 'videos.db'

# Credenciais Admin (MUITO INSEGURO PARA PRODUÇÃO - USE HASHING DE SENHA E VARIÁVEIS DE AMBIENTE)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin') # A senha 'admin' será hasheada.

# Cria a pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Funções do Banco de Dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Isso permite acessar colunas por nome
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cria a tabela 'videos' se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            seo_keywords TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0
        )
    ''')
    
    # Adiciona a coluna 'views' se ela não existir (para garantir compatibilidade com versões anteriores)
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN views INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        # Coluna já existe, ignora o erro
        pass
        
    # Cria a tabela 'site_settings' para SEO geral
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT
        )
    ''')
    
    # Insere configurações padrão de SEO se não existirem
    settings = {
        'meta_title_general': 'Seus Vídeos - Entretenimento de Qualidade',
        'meta_description_general': 'Descubra uma vasta coleção de vídeos de alta qualidade. Filmes, séries, tutoriais e muito mais!',
        'meta_keywords_general': 'vídeos, entretenimento, online, streaming, filmes, séries'
    }
    for name, value in settings.items():
        cursor.execute("INSERT OR IGNORE INTO site_settings (setting_name, setting_value) VALUES (?, ?)", (name, value))

    conn.commit()
    conn.close()

# Inicializa o banco de dados na primeira execução
with app.app_context():
    init_db()

# Função para buscar configurações de SEO gerais
def get_site_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_name, setting_value FROM site_settings")
    settings = {row['setting_name']: row['setting_value'] for row in cursor.fetchall()}
    conn.close()
    return settings

# --- Rotas da Aplicação ---

# Middleware para verificação de idade
@app.before_request
def check_age_and_session():
    # Permite acesso à página de verificação de idade, arquivos estáticos e página de login admin
    if 'age_verified' not in session and request.endpoint not in ['age_gate', 'verify_age', 'static', 'admin_login']:
        return redirect(url_for('age_gate'))

# Rota para o pop-up de verificação de idade
@app.route('/age_gate')
def age_gate():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verificação de Idade</title>
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .age-gate-container { text-align: center; padding: 50px; background-color: #333; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); max-width: 500px; }
            .age-gate-container h1 { color: #ff9900; }
            .age-gate-container p { margin-bottom: 30px; font-size: 1.1em; }
            .age-gate-container button { background-color: #ff9900; color: white; border: none; padding: 12px 25px; margin: 0 10px; border-radius: 5px; cursor: pointer; font-size: 1.1em; transition: background-color 0.3s; }
            .age-gate-container button:hover { background-color: #cc7a00; }
        </style>
    </head>
    <body>
        <div class="age-gate-container">
            <h1>Confirmação de Idade</h1>
            <p>Este site pode conter conteúdo adulto. Você confirma ter mais de 18 anos?</p>
            <form action="{{ url_for('verify_age') }}" method="post">
                <button type="submit" name="age_confirm" value="yes">Sim, eu tenho 18 anos ou mais</button>
                <button type="submit" name="age_confirm" value="no">Não</button>
            </form>
        </div>
    </body>
    </html>
    ''')

# Rota para processar a verificação de idade
@app.route('/verify_age', methods=['POST'])
def verify_age():
    if request.form.get('age_confirm') == 'yes':
        session['age_verified'] = True
        return redirect(url_for('index'))
    else:
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Acesso Negado</title>
            <style>
                body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
                .denied-container { text-align: center; padding: 50px; background-color: #333; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); max-width: 500px; }
                .denied-container h1 { color: #ff0000; }
                .denied-container p { font-size: 1.2em; }
            </style>
        </head>
        <body>
            <div class="denied-container">
                <h1>Acesso Negado</h1>
                <p>Você deve ter 18 anos ou mais para acessar este conteúdo.</p>
            </div>
        </body>
        </html>
        ''')

# Rota para a página do cliente (exibir vídeos)
@app.route('/')
def index():
    if 'age_verified' not in session:
        return redirect(url_for('age_gate'))

    conn = get_db_connection()
    cursor = conn.cursor()
    search_query = request.args.get('search', '').strip() # Remove espaços em branco
    
    if search_query:
        # Pesquisa por título, descrição ou palavras-chave SEO
        cursor.execute("SELECT * FROM videos WHERE title LIKE ? OR description LIKE ? OR seo_keywords LIKE ? ORDER BY upload_date DESC",
                       (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("SELECT * FROM videos ORDER BY upload_date DESC")
    
    videos = cursor.fetchall()
    conn.close()

    site_settings = get_site_settings()
    
    # HTML da página do cliente
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ site_settings['meta_title_general'] }}</title>
        <meta name="description" content="{{ site_settings['meta_description_general'] }}">
        <meta name="keywords" content="{{ site_settings['meta_keywords_general'] }}">
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }
            header { background-color: #1c1c1c; padding: 1rem 0; text-align: center; border-bottom: 3px solid #000; }
            header h1 { margin: 0; color: #ff9900; font-size: 2.5em; text-transform: uppercase; letter-spacing: 2px; }
            nav { margin-top: 10px; }
            nav a { color: #e5c100; text-decoration: none; margin: 0 15px; font-weight: bold; transition: color 0.3s; }
            nav a:hover { color: #ff9900; }
            main { padding: 20px; max-width: 1400px; margin: 20px auto; background-color: #2b2b2b; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); }
            
            .search-bar { margin-bottom: 30px; text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px; }
            .search-bar input[type="text"] { flex-grow: 1; max-width: 600px; padding: 12px 15px; border: 1px solid #555; border-radius: 25px; background-color: #444; color: #f0f0f0; font-size: 1.1em; outline: none; transition: border-color 0.3s; }
            .search-bar input[type="text"]:focus { border-color: #ff9900; }
            .search-bar button { background-color: #ff9900; color: white; border: none; padding: 12px 25px; border-radius: 25px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background-color 0.3s; }
            .search-bar button:hover { background-color: #e5c100; }

            .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }
            .video-item { background-color: #333; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); transition: transform 0.2s, box-shadow 0.2s; position: relative; }
            .video-item:hover { transform: translateY(-8px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.8); }
            .video-item a { text-decoration: none; color: inherit; display: block; }
            .video-item video { width: 100%; height: 180px; object-fit: cover; display: block; border-bottom: 2px solid #444; }
            .video-item .info { padding: 15px; }
            .video-item h2 { font-size: 1.3em; margin: 0 0 8px; color: #ff9900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .video-item p.views { font-size: 0.9em; color: #ccc; margin: 0; }
            .no-videos { text-align: center; font-size: 1.4em; color: #ccc; padding: 50px; }

            /* Detalhe do Vídeo */
            .video-player { margin-bottom: 30px; }
            .video-player video { width: 100%; max-height: 600px; display: block; border-radius: 8px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.7); }
            .video-info { background-color: #333; padding: 25px; border-radius: 8px; }
            .video-info h2 { color: #ff9900; margin-top: 0; font-size: 2em; }
            .video-info p { margin-bottom: 12px; line-height: 1.6; color: #ccc; }
            .video-info p strong { color: #e5c100; }
        </style>
    </head>
    <body>
        <header>
            <h1>SEUS VÍDEOS</h1>
            <nav>
                <a href="{{ url_for('index') }}">Página Principal</a>
            </nav>
        </header>
        <main>
            <div class="search-bar">
                <form action="{{ url_for('index') }}" method="get">
                    <input type="text" name="search" placeholder="Pesquisar vídeos..." value="{{ search_query }}">
                    <button type="submit">Pesquisar</button>
                </form>
            </div>

            <div class="video-grid">
                {% if videos %}
                    {% for video in videos %}
                    <div class="video-item">
                        <a href="{{ url_for('video_detail', video_id=video['id']) }}">
                            <video controls preload="metadata">
                                <source src="{{ url_for('static', filename='videos/' + video['filename']) }}" type="video/mp4">
                                Seu navegador não suporta a tag de vídeo.
                            </video>
                            <div class="info">
                                <h2>{{ video['title'] }}</h2>
                                <p class="views">Visualizações: {{ video['views'] }}</p>
                            </div>
                        </a>
                    </div>
                    {% endfor %}
                {% else %}
                    <p class="no-videos">Nenhum vídeo encontrado. Comece a postar!</p>
                {% endif %}
            </div>
        </main>
    </body>
    </html>
    ''', videos=videos, search_query=search_query, site_settings=site_settings)

# Rota para a página de detalhes do vídeo
@app.route('/video/<int:video_id>')
def video_detail(video_id):
    if 'age_verified' not in session:
        return redirect(url_for('age_gate'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    
    if video:
        # Incrementa a contagem de visualizações
        cursor.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))
        conn.commit()
        # Recarrega o vídeo para mostrar a visualização atualizada
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        video = cursor.fetchone() 
    conn.close()

    if video:
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ video['title'] }}</title>
            <style>
                body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }
                header { background-color: #1c1c1c; padding: 1rem 0; text-align: center; border-bottom: 3px solid #000; }
                header h1 { margin: 0; color: #ff9900; font-size: 2.5em; text-transform: uppercase; letter-spacing: 2px; }
                nav { margin-top: 10px; }
                nav a { color: #e5c100; text-decoration: none; margin: 0 15px; font-weight: bold; transition: color 0.3s; }
                nav a:hover { color: #ff9900; }
                main { padding: 20px; max-width: 1200px; margin: 20px auto; background-color: #2b2b2b; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); }
                .video-player { margin-bottom: 30px; }
                .video-player video { width: 100%; max-height: 600px; display: block; border-radius: 8px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.7); }
                .video-info { background-color: #333; padding: 25px; border-radius: 8px; }
                .video-info h2 { color: #ff9900; margin-top: 0; font-size: 2em; }
                .video-info p { margin-bottom: 12px; line-height: 1.6; color: #ccc; }
                .video-info p strong { color: #e5c100; }
            </style>
        </head>
        <body>
            <header>
                <h1>{{ video['title'] }}</h1>
                <nav>
                    <a href="{{ url_for('index') }}">Voltar para a Página Principal</a>
                </nav>
            </header>
            <main>
                <div class="video-player">
                    <video controls>
                        <source src="{{ url_for('static', filename='videos/' + video['filename']) }}" type="video/mp4">
                        Seu navegador não suporta a tag de vídeo.
                    </video>
                </div>
                <div class="video-info">
                    <h2>{{ video['title'] }}</h2>
                    <p><strong>Descrição:</strong> {{ video['description'] if video['description'] else 'Sem descrição' }}</p>
                    <p><strong>Palavras-chave SEO:</strong> {{ video['seo_keywords'] if video['seo_keywords'] else 'Nenhuma' }}</p>
                    <p><strong>Data de Envio:</strong> {{ video['upload_date'] }}</p>
                    <p><strong>Visualizações:</strong> {{ video['views'] }}</p>
                </div>
            </main>
        </body>
        </html>
        ''', video=video)
    return "Vídeo não encontrado", 404

# Rota para a página de login do administrador
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            flash('Login de administrador bem-sucedido!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Administrativo</title>
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .login-container { text-align: center; padding: 50px; background-color: #333; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); max-width: 400px; }
            .login-container h1 { color: #ff9900; margin-bottom: 30px; }
            .login-container label { display: block; text-align: left; margin-bottom: 5px; color: #ccc; }
            .login-container input[type="text"], .login-container input[type="password"] {
                width: calc(100% - 22px);
                padding: 10px;
                margin-bottom: 15px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #444;
                color: #f0f0f0;
                font-size: 1em;
            }
            .login-container button[type="submit"] {
                background-color: #ff9900;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1.1em;
                transition: background-color 0.3s;
            }
            .login-container button[type="submit"]:hover { background-color: #cc7a00; }
            .flashes { list-style: none; padding: 0; margin-top: 15px; }
            .flashes li { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
            .flashes li.danger { background-color: #f8d7da; color: #721c24; }
            .flashes li.success { background-color: #d4edda; color: #155724; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Login Administrativo</h1>
            <form action="{{ url_for('admin_login') }}" method="post">
                <label for="username">Usuário:</label>
                <input type="text" id="username" name="username" required>
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" required>
                <button type="submit">Entrar</button>
            </form>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="flashes">
                        {% for category, message in messages %}
                            <li class="{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}
        </div>
    </body>
    </html>
    ''')


# Rota para a área administrativa (upload de vídeos e gerenciamento)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        seo_keywords = request.form.get('seo_keywords', '')
        
        if 'video_file' not in request.files:
            flash('Nenhum arquivo de vídeo selecionado!', 'danger')
            return redirect(request.url)
        
        video_file = request.files['video_file']
        
        if video_file.filename == '':
            flash('Nenhum arquivo selecionado para upload!', 'danger')
            return redirect(request.url)
        
        filename = video_file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Garante que o nome do arquivo seja único para evitar sobrescrita
        counter = 1
        original_name, file_ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{original_name}_{counter}{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            counter += 1

        video_file.save(filepath)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (title, description, filename, seo_keywords) VALUES (?, ?, ?, ?)",
                       (title, description, filename, seo_keywords))
        conn.commit()
        conn.close()
        flash('Vídeo enviado com sucesso!', 'success')
        return redirect(url_for('admin'))
    
    # HTML da página admin (formulário de upload e listagem)
    conn = get_db_connection()
    videos = conn.execute("SELECT * FROM videos ORDER BY upload_date DESC").fetchall()
    
    # Calcular total de visualizações
    cursor = conn.cursor()
    total_views_row = cursor.execute("SELECT SUM(views) FROM videos").fetchone()
    total_views = total_views_row[0] if total_views_row[0] is not None else 0
    
    conn.close()

    # Usando render_template_string para o HTML diretamente no Python
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Área Administrativa - Postar Vídeo</title>
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }
            header { background-color: #1c1c1c; padding: 1rem 0; text-align: center; border-bottom: 3px solid #000; }
            header h1 { margin: 0; color: #ff9900; font-size: 2.5em; text-transform: uppercase; letter-spacing: 2px; }
            nav { margin-top: 10px; }
            nav a { color: #e5c100; text-decoration: none; margin: 0 15px; font-weight: bold; transition: color 0.3s; }
            nav a:hover { color: #ff9900; }
            main { padding: 20px; max-width: 900px; margin: 20px auto; background-color: #2b2b2b; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); }
            form { background-color: #333; padding: 25px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); }
            form label { display: block; margin-bottom: 8px; color: #f0f0f0; font-weight: bold; }
            form input[type="text"], form textarea, form input[type="file"] { 
                width: calc(100% - 22px); 
                padding: 12px; 
                margin-bottom: 15px; 
                border: 1px solid #555; 
                border-radius: 5px; 
                background-color: #444; 
                color: #f0f0f0; 
                font-size: 1em;
                outline: none;
                transition: border-color 0.3s;
            }
            form input[type="text"]:focus, form textarea:focus, form input[type="file"]:focus { border-color: #ff9900; }
            form textarea { resize: vertical; min-height: 80px; }
            form button[type="submit"] { background-color: #ff9900; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background-color 0.3s; }
            form button[type="submit"]:hover { background-color: #e5c100; }
            .flashes { list-style: none; padding: 0; margin-top: 20px; }
            .flashes li { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
            .flashes li.success { background-color: #d4edda; color: #155724; }
            .flashes li.danger { background-color: #f8d7da; color: #721c24; }
            .flashes li.warning { background-color: #fff3cd; color: #856404; }
            h2 { color: #ff9900; border-bottom: 2px solid #e5c100; padding-bottom: 8px; margin-top: 30px; font-size: 1.8em; }
            .admin-stats { background-color: #333; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
            .admin-stats p { margin: 5px 0; font-size: 1.1em; }
            .admin-stats p strong { color: #e5c100; }
            .video-list ul { list-style: none; padding: 0; }
            .video-list li { background-color: #333; padding: 15px; margin-bottom: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); }
            .video-list li strong { color: #ff9900; font-size: 1.1em; }
            .video-list li .info { flex-grow: 1; margin-right: 15px; }
            .video-list li small { color: #ccc; font-size: 0.9em; }
            .video-list li .actions { display: flex; gap: 10px; }
            .video-list li .actions a { color: #fff; text-decoration: none; background-color: #007bff; padding: 8px 15px; border-radius: 5px; transition: background-color 0.3s; }
            .video-list li .actions a.delete { background-color: #dc3545; }
            .video-list li .actions a:hover { opacity: 0.9; }
        </style>
    </head>
    <body>
        <header>
            <h1>PAINEL ADMINISTRATIVO</h1>
            <nav>
                <a href="{{ url_for('index') }}">Ver Página de Cliente</a>
                <a href="{{ url_for('admin') }}">Postar Novo Vídeo</a>
                <a href="{{ url_for('admin_seo') }}">SEO Geral do Site</a>
                <a href="{{ url_for('admin_logout') }}">Sair</a>
            </nav>
        </header>
        <main>
            <div class="admin-stats">
                <p>Total de Vídeos: <strong>{{ videos|length }}</strong></p>
                <p>Total de Visualizações: <strong>{{ total_views }}</strong></p>
            </div>

            <h2>Postar Novo Vídeo</h2>
            <form action="{{ url_for('admin') }}" method="post" enctype="multipart/form-data">
                <label for="title">Título do Vídeo:</label>
                <input type="text" id="title" name="title" required>

                <label for="description">Descrição (opcional):</label>
                <textarea id="description" name="description"></textarea>

                <label for="seo_keywords">Palavras-chave SEO (separadas por vírgula, opcional):</label>
                <input type="text" id="seo_keywords" name="seo_keywords">

                <label for="video_file">Arquivo de Vídeo (MP4 recomendado):</label>
                <input type="file" id="video_file" name="video_file" accept="video/mp4" required>

                <button type="submit">Enviar Vídeo</button>
            </form>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="flashes">
                        {% for category, message in messages %}
                            <li class="{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}

            <h2>Vídeos Existentes</h2>
            <div class="video-list">
                <ul>
                    {% if videos %}
                        {% for video in videos %}
                            <li>
                                <div class="info">
                                    <strong>{{ video['title'] }}</strong><br>
                                    <small>Nome do Arquivo: {{ video['filename'] }}</small><br>
                                    <small>Visualizações: {{ video['views'] }}</small>
                                </div>
                                <div class="actions">
                                    <a href="{{ url_for('video_detail', video_id=video['id']) }}">Ver</a>
                                    <a href="{{ url_for('delete_video', video_id=video['id']) }}" class="delete" onclick="return confirm('Tem certeza que deseja deletar este vídeo?');">Deletar</a>
                                </div>
                            </li>
                        {% endfor %}
                    {% else %}
                        <li>Nenhum vídeo postado ainda.</li>
                    {% endif %}
                </ul>
            </div>
        </main>
    </body>
    </html>
    ''', videos=videos, total_views=total_views)

# Rota para fazer logout do administrador
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('admin_login'))

# Rota para a página de SEO geral do site
@app.route('/admin/seo', methods=['GET', 'POST'])
def admin_seo():
    if not session.get('admin_logged_in'):
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    site_settings = get_site_settings()

    if request.method == 'POST':
        meta_title = request.form['meta_title_general']
        meta_description = request.form['meta_description_general']
        meta_keywords = request.form['meta_keywords_general']

        cursor = conn.cursor()
        cursor.execute("REPLACE INTO site_settings (setting_name, setting_value) VALUES (?, ?)", ('meta_title_general', meta_title))
        cursor.execute("REPLACE INTO site_settings (setting_name, setting_value) VALUES (?, ?)", ('meta_description_general', meta_description))
        cursor.execute("REPLACE INTO site_settings (setting_name, setting_value) VALUES (?, ?)", ('meta_keywords_general', meta_keywords))
        conn.commit()
        conn.close()
        flash('Configurações de SEO gerais salvas com sucesso!', 'success')
        return redirect(url_for('admin_seo'))
    
    conn.close()

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Área Administrativa - SEO Geral</title>
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }
            header { background-color: #1c1c1c; padding: 1rem 0; text-align: center; border-bottom: 3px solid #000; }
            header h1 { margin: 0; color: #ff9900; font-size: 2.5em; text-transform: uppercase; letter-spacing: 2px; }
            nav { margin-top: 10px; }
            nav a { color: #e5c100; text-decoration: none; margin: 0 15px; font-weight: bold; transition: color 0.3s; }
            nav a:hover { color: #ff9900; }
            main { padding: 20px; max-width: 900px; margin: 20px auto; background-color: #2b2b2b; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.7); }
            form { background-color: #333; padding: 25px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); }
            form label { display: block; margin-bottom: 8px; color: #f0f0f0; font-weight: bold; }
            form input[type="text"], form textarea { 
                width: calc(100% - 22px); 
                padding: 12px; 
                margin-bottom: 15px; 
                border: 1px solid #555; 
                border-radius: 5px; 
                background-color: #444; 
                color: #f0f0f0; 
                font-size: 1em;
                outline: none;
                transition: border-color 0.3s;
            }
            form input[type="text"]:focus, form textarea:focus { border-color: #ff9900; }
            form textarea { resize: vertical; min-height: 80px; }
            form button[type="submit"] { background-color: #ff9900; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background-color 0.3s; }
            form button[type="submit"]:hover { background-color: #e5c100; }
            .flashes { list-style: none; padding: 0; margin-top: 20px; }
            .flashes li { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
            .flashes li.success { background-color: #d4edda; color: #155724; }
            .flashes li.danger { background-color: #f8d7da; color: #721c24; }
            .flashes li.warning { background-color: #fff3cd; color: #856404; }
            h2 { color: #ff9900; border-bottom: 2px solid #e5c100; padding-bottom: 8px; margin-top: 30px; font-size: 1.8em; }
        </style>
    </head>
    <body>
        <header>
            <h1>PAINEL ADMINISTRATIVO</h1>
            <nav>
                <a href="{{ url_for('index') }}">Ver Página de Cliente</a>
                <a href="{{ url_for('admin') }}">Postar Novo Vídeo</a>
                <a href="{{ url_for('admin_seo') }}">SEO Geral do Site</a>
                <a href="{{ url_for('admin_logout') }}">Sair</a>
            </nav>
        </header>
        <main>
            <h2>Configurações de SEO Geral do Site</h2>
            <form action="{{ url_for('admin_seo') }}" method="post">
                <label for="meta_title_general">Meta Título do Site:</label>
                <input type="text" id="meta_title_general" name="meta_title_general" value="{{ site_settings['meta_title_general'] }}" required>

                <label for="meta_description_general">Meta Descrição do Site:</label>
                <textarea id="meta_description_general" name="meta_description_general" required>{{ site_settings['meta_description_general'] }}</textarea>

                <label for="meta_keywords_general">Meta Palavras-chave do Site (separadas por vírgula):</label>
                <input type="text" id="meta_keywords_general" name="meta_keywords_general" value="{{ site_settings['meta_keywords_general'] }}">

                <button type="submit">Salvar Configurações de SEO</button>
            </form>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <ul class="flashes">
                        {% for category, message in messages %}
                            <li class="{{ category }}">{{ message }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            {% endwith %}
        </main>
    </body>
    </html>
    ''', site_settings=site_settings)


# Rota para deletar vídeos
@app.route('/admin/delete/<int:video_id>')
def delete_video(video_id):
    if not session.get('admin_logged_in'):
        flash('Você precisa fazer login para realizar esta ação.', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Pega o nome do arquivo antes de deletar do DB
    cursor.execute("SELECT filename FROM videos WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    
    if video:
        filename = video['filename']
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Deleta do banco de dados
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()
        
        # Deleta o arquivo do servidor
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f'Vídeo "{filename}" e seus dados deletados com sucesso!', 'success')
        else:
            flash(f'Dados do vídeo deletados, mas o arquivo "{filename}" não foi encontrado no servidor.', 'warning')
    else:
        flash('Vídeo não encontrado para deletar.', 'danger')

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
