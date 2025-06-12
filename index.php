<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Conexão com banco Railway
try {
    $pdo = new PDO(
        "mysql:host=tramway.proxy.rlwy.net;port=12027;dbname=railway;charset=utf8mb4",
        "root",
        "nLrLybfKaZucSbtMIMDtoTiJKjTdCYWq"
    );
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro na conexão com o banco de dados: " . $e->getMessage());
}

// Função de registro de visitas
function logVisit($pdo, $page) {
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'desconhecido';
    $agent = $_SERVER['HTTP_USER_AGENT'] ?? 'desconhecido';

    $stmt = $pdo->prepare("INSERT INTO visits (page, ip_address, user_agent) VALUES (?, ?, ?)");
    $stmt->execute([$page, $ip, $agent]);
}

// Lógica de rota e verificação de login
$route = $_GET['route'] ?? 'home';
if (!isset($_SESSION['user_id']) && !in_array($route, ['login', 'register', 'home'])) {
    header("Location: ?route=login");
    exit;
}

logVisit($pdo, $route);

// Roteamento
switch ($route) {
    case 'home':
        require 'home.php';
        break;
    case 'login':
        require 'login.php';
        break;
    case 'register':
        require 'register.php';
        break;
    case 'feed':
        require 'feed.php';
        break;
    case 'profile':
        require 'profile.php';
        break;
    case 'chat':
        require 'chat.php';
        break;
    case 'admin':
        require 'admin.php';
        break;
    case 'marketplace':
        require 'marketplace.php';
        break;
    case 'logout':
        require 'logout.php';
        break;
    case 'search':
        require 'search.php';
        break;
    default:
        echo "<h1>Página não encontrada</h1>";
        break;
}
?>

<?php if (isset($_SESSION['user_id'])): ?>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
/* SEU CSS ORIGINAL AQUI - MENU E POPUP DE BUSCA */
.nav-menu {
    position: fixed;
    background-color: #fff;
    border-right: 1px solid #ccc;
    width: 70px;
    height: 100vh;
    top: 0;
    left: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 60px;
    z-index: 1000;
}
.nav-menu a, .nav-menu button {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 20px 0;
    color: #333;
    text-decoration: none;
    font-size: 14px;
    background: none;
    border: none;
    cursor: pointer;
}
.nav-menu i {
    font-size: 22px;
    margin-bottom: 5px;
}
@media (max-width: 768px) {
    .nav-menu {
        flex-direction: row;
        width: 100%;
        height: 60px;
        bottom: 0;
        top: auto;
        left: 0;
        border-right: none;
        border-top: 1px solid #ccc;
        justify-content: space-around;
        padding: 0;
    }
}

/* Popup de pesquisa */
#search-popup {
    position: fixed;
    top: 0;
    left: 70px;
    width: calc(100% - 70px);
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.95);
    color: white;
    z-index: 1500;
    display: none;
    flex-direction: column;
    padding: 20px;
    box-sizing: border-box;
}
@media (max-width: 768px) {
    #search-popup {
        top: 0;
        left: 0;
        width: 100%;
        height: calc(100vh - 60px);
        padding-bottom: 60px;
    }
}
#search-popup-input {
    background: #111;
    color: white;
    border: 1px solid #333;
    padding: 15px;
    font-size: 16px;
    width: 100%;
    margin-bottom: 15px;
    border-radius: 8px;
}
#search-popup-results {
    overflow-y: auto;
    max-height: calc(100vh - 120px);
    padding: 10px;
}
#search-popup-results .user-result {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #222;
    cursor: pointer;
    transition: background-color 0.2s;
}
#search-popup-results .user-result:hover {
    background-color: rgba(255, 255, 255, 0.05);
}
#search-popup-results .user-result img {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    margin-right: 15px;
    object-fit: cover;
    border: 2px solid #333;
}
#search-popup-results .user-result span {
    color: #fff;
    font-size: 16px;
    font-weight: 500;
}
.no-results {
    color: #888;
    text-align: center;
    padding: 20px;
    font-size: 16px;
}
.close-search {
    position: absolute;
    top: 15px;
    right: 15px;
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
}
</style>

<!-- Popup de pesquisa -->
<div id="search-popup">
    <button class="close-search" onclick="toggleSearch()">×</button>
    <input type="text" id="search-popup-input" placeholder="Buscar usuários..." autocomplete="off" />
    <div id="search-popup-results"></div>
</div>

<!-- Menu de navegação -->
<div class="nav-menu">
    <button onclick="toggleSearch()" title="Buscar"><i class="fas fa-magnifying-glass"></i><span class="label">Buscar</span></button>
    <a href="?route=feed" title="Feed"><i class="fas fa-house"></i><span class="label">Feed</span></a>
    <a href="?route=marketplace" title="Loja"><i class="fas fa-store"></i><span class="label">Loja</span></a>
    <a href="?route=profile" title="Perfil"><i class="fas fa-user"></i><span class="label">Perfil</span></a>
    <a href="?route=chat" title="Chat"><i class="fas fa-comments"></i><span class="label">Chat</span></a>
    <a href="?route=logout" title="Sair"><i class="fas fa-sign-out-alt"></i><span class="label">Sair</span></a>
</div>

<script>
let searchTimeout;

function toggleSearch() {
    const popup = document.getElementById('search-popup');
    if (!popup) return;

    if (popup.style.display === 'flex') {
        popup.style.display = 'none';
        document.getElementById('search-popup-input').value = '';
        document.getElementById('search-popup-results').innerHTML = '';
    } else {
        popup.style.display = 'flex';
        const input = document.getElementById('search-popup-input');
        if (input) input.focus();
    }
}

document.getElementById('search-popup-input').addEventListener('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(buscarUsuarios, 300);
});

function buscarUsuarios() {
    const q = document.getElementById('search-popup-input').value.trim();
    const results = document.getElementById('search-popup-results');

    if (q.length === 0) {
        results.innerHTML = '';
        return;
    }

    fetch('buscar_usuarios.php?q=' + encodeURIComponent(q))
        .then(res => res.json())
        .then(data => {
            results.innerHTML = '';

            if (!Array.isArray(data) || data.length === 0) {
                results.innerHTML = '<div class="no-results">Nenhum usuário encontrado</div>';
                return;
            }

            data.forEach(user => {
                const div = document.createElement('div');
                div.className = 'user-result';
                div.innerHTML = `
                    <img src="${user.profile_picture || 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png'}" 
                         onerror="this.src='https://cdn-icons-png.flaticon.com/512/4140/4140048.png'">
                    <span>@${user.username}</span>
                `;
                div.addEventListener('click', () => {
                    window.location.href = `?route=profile&user_id=${user.id}`;
                });
                results.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Erro na busca:', error);
            results.innerHTML = '<div class="no-results">Erro ao buscar usuários</div>';
        });
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        toggleSearch();
    }
});
</script>
<?php endif; ?>
