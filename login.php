<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'login');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = filter_input(INPUT_POST, 'username', FILTER_SANITIZE_STRING);
    $password = $_POST['password'];

    $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ? OR email = ?");
    $stmt->execute([$username, $username]);
    $user = $stmt->fetch();

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['id'];
        $_SESSION['username'] = $user['username'];
        $_SESSION['is_admin'] = ($user['username'] === 'admin');
        header("Location: ?route=feed");
        exit;
    } else {
        $error = "Credenciais inválidas.";
    }
}
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --secondary: #f3f4f6;
            --dark-bg: #000000;
            --dark-card: #1e1e1e;
            --dark-text: #ffffff;
            --dark-border: #444444;
            --light-bg: #f8f9fa;
            --light-card: #ffffff;
            --light-text: #333333;
            --light-border: #e5e7eb;
        }
        .dark {
            background-color: var(--dark-bg);
            color: var(--dark-text);
        }
        .dark .navbar, .dark .post-card, .dark .form-control, .dark .form-select {
            background-color: var(--dark-card);
            border-color: var(--dark-border);
            color: var(--dark-text);
        }
        .dark .text-gray-500 { color: #a0a0a0 !important; }
        .dark .text-gray-300 { color: #d0d0d0 !important; }
        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-color: var(--light-bg);
            color: var(--light-text);
        }
        .dark body {
            background-color: var(--dark-bg);
            color: var(--dark-text);
        }
        .navbar {
            background-color: var(--light-card);
            border-bottom: 1px solid var(--light-border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .post-card {
            border: 1px solid #ffffff;
            background-color: var(--light-card);
            margin-bottom: 20px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .footer {
            background-color: var(--light-card);
            padding: 20px 0;
            margin-top: auto;
            border-top: 1px solid var(--light-border);
        }
        .dark .footer {
            background-color: var(--dark-card);
            border-top: 1px solid var(--dark-border);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand font-bold text-xl" href="?route=home">Evoluir</a>
            <div class="navbar-nav flex-row">
                <?php if (isset($_SESSION['user_id'])): ?>
                    <form class="d-flex mx-auto search-form" method="GET" action="?route=search">
                        <input type="hidden" name="route" value="search">
                        <input class="form-control rounded-full w-64" type="text" name="query" placeholder="Pesquisar perfis..." aria-label="Search">
                    </form>
                    <a class="nav-link px-3" href="?route=feed"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg></a>
                    <a class="nav-link px-3" href="?route=profile"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg></a>
                    <a class="nav-link px-3" href="?route=marketplace"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg></a>
                    <a class="nav-link px-3" href="?route=chat"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg></a>
                    <?php if (isset($_SESSION['is_admin']) && $_SESSION['is_admin']): ?>
                        <a class="nav-link px-3" href="?route=admin"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path></svg></a>
                    <?php endif; ?>
                    <a class="nav-link px-3" href="?route=logout"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg></a>
                <?php else: ?>
                    <a class="nav-link px-3" href="?route=login">Login</a>
                    <a class="nav-link px-3" href="?route=register">Cadastrar</a>
                <?php endif; ?>
                <a class="nav-link px-3" href="?theme=<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'light' : 'dark'; ?>">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <?php if (isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark'): ?>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
                        <?php else: ?>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
                        <?php endif; ?>
                    </svg>
                </a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto mt-16 px-4 flex-grow">
        <?php if (isset($error)): ?>
            <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <div class="max-w-md mx-auto post-card p-6">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold mb-2">Login</h2>
                <p class="text-sm text-gray-500">Acesse sua conta para começar a evoluir</p>
            </div>
            <form method="POST" action="?route=login">
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Usuário ou Email</label>
                    <input type="text" class="form-control w-full p-2 border rounded" name="username" required>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Senha</label>
                    <input type="password" class="form-control w-full p-2 border rounded" name="password" required>
                </div>
                <div class="mb-4 flex justify-between items-center">
                    <div class="flex items-center">
                        <input type="checkbox" id="remember" name="remember" class="mr-2">
                        <label for="remember" class="text-sm">Lembrar de mim</label>
                    </div>
                    <a href="#" class="text-sm text-blue-500">Esqueceu a senha?</a>
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition">Entrar</button>
            </form>
            <p class="text-center mt-4">Não tem uma conta? <a href="?route=register" class="text-blue-500">Cadastre-se</a></p>
        </div>
    </div>

    <footer class="footer">
        <div class="container mx-auto px-4 py-6">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="mb-4 md:mb-0 text-center md:text-left">
                    <a href="?route=home" class="font-bold text-xl">Evoluir</a>
                    <p class="text-sm mt-1">Transformando vidas através da educação financeira e networking</p>
                </div>
                <div class="flex flex-wrap justify-center gap-4">
                    <a href="#" class="text-sm hover:text-blue-500">Sobre</a>
                    <a href="#" class="text-sm hover:text-blue-500">Termos</a>
                    <a href="#" class="text-sm hover:text-blue-500">Privacidade</a>
                    <a href="#" class="text-sm hover:text-blue-500">Contato</a>
                </div>
            </div>
            <div class="text-center mt-6 text-sm text-gray-500">
                &copy; <?php echo date('Y'); ?> Evoluir. Todos os direitos reservados.
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const themeToggle = document.querySelector('[href*="theme="]');
            if (themeToggle) {
                themeToggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    document.documentElement.classList.add('transition-colors', 'duration-300');
                    document.documentElement.classList.toggle('dark');
                    setTimeout(() => {
                        window.location.href = this.href;
                    }, 300);
                });
            }
        });
    </script>
</body>
</html>