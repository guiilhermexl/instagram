<?php
session_start();
require_once 'db_connect.php';
logVisit($pdo, 'admin');

if (!isset($_SESSION['user_id']) || !isset($_SESSION['is_admin']) || !$_SESSION['is_admin']) {
    header("Location: ?route=home");
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['delete_user'])) {
        $user_id = (int)$_POST['user_id'];
        $stmt = $pdo->prepare("DELETE FROM users WHERE id = ?");
        $stmt->execute([$user_id]);
    } elseif (isset($_POST['delete_post'])) {
        $post_id = (int)$_POST['post_id'];
        $stmt = $pdo->prepare("DELETE FROM posts WHERE id = ?");
        $stmt->execute([$post_id]);
    } elseif (isset($_POST['delete_service'])) {
        $service_id = (int)$_POST['service_id'];
        $stmt = $pdo->prepare("DELETE FROM services WHERE id = ?");
        $stmt->execute([$service_id]);
    }
    header("Location: ?route=admin");
    exit;
}

$users = $pdo->query("SELECT * FROM users WHERE id != ? ORDER BY username ASC")->fetchAll(PDO::FETCH_ASSOC);
$posts = $pdo->query("SELECT p.*, u.username FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC")->fetchAll(PDO::FETCH_ASSOC);
$services = $pdo->query("SELECT s.*, u.username FROM services s JOIN users u ON s.user_id = u.id ORDER BY s.created_date DESC")->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Administração</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap" rel="stylesheet">
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
        .dark .navbar, .dark .post-card, .dark .form-control, .dark .table {
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
        .table {
            border: 1px solid #ffffff;
            background-color: var(--light-card);
        }
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .btn-danger {
            background-color: #dc3545;
            border-color: #dc3545;
        }
        .btn-danger:hover {
            background-color: #c82333;
            border-color: #c82333;
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
                <form class="d-flex mx-auto search-form" method="GET" action="?route=search">
                    <input type="hidden" name="route" value="search">
                    <input class="form-control rounded-full w-64" type="text" name="query" placeholder="Pesquisar perfis..." aria-label="Search">
                </form>
                <a class="nav-link px-3" href="?route=feed"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg></a>
                <a class="nav-link px-3" href="?route=profile"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg></a>
                <a class="nav-link px-3" href="?route=marketplace"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 0z"></path></svg></a>
                <a class="nav-link px-3" href="?route=chat"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg></a>
                <a class="nav-link px-3" href="?route=admin"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path></svg></a>
                <a class="nav-link px-3" href="?route=logout"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg></a>
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
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold mb-6">Painel Administrativo</h2>

            <!-- Gerenciamento de Usuários -->
            <div class="post-card p-4 mb-6">
                <h3 class="text-xl font-bold mb-4">Usuários</h3>
                <table class="table w-full">
                    <thead>
                        <tr>
                            <th>Usuário</th>
                            <th>Email</th>
                            <th>Data de Cadastro</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($users as $user): ?>
                            <tr>
                                <td>@<?php echo htmlspecialchars($user['username']); ?></td>
                                <td><?php echo htmlspecialchars($user['email']); ?></td>
                                <td><?php echo date('d/m/Y', strtotime($user['created_at'])); ?></td>
                                <td>
                                    <form method="POST" onsubmit="return confirm('Tem certeza que deseja excluir este usuário?');">
                                        <input type="hidden" name="user_id" value="<?php echo $user['id']; ?>">
                                        <button type="submit" name="delete_user" class="btn btn-danger btn-sm">Excluir</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>

            <!-- Gerenciamento de Postagens -->
            <div class="post-card p-4 mb-6">
                <h3 class="text-xl font-bold mb-4">Postagens</h3>
                <table class="table w-full">
                    <thead>
                        <tr>
                            <th>Autor</th>
                            <th>Conteúdo</th>
                            <th>Data</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($posts as $post): ?>
                            <tr>
                                <td>@<?php echo htmlspecialchars($post['username']); ?></td>
                                <td><?php echo htmlspecialchars(substr($post['content'], 0, 50)) . '...'; ?></td>
                                <td><?php echo date('d/m/Y H:i', strtotime($post['created_at'])); ?></td>
                                <td>
                                    <form method="POST" onsubmit="return confirm('Tem certeza que deseja excluir esta postagem?');">
                                        <input type="hidden" name="post_id" value="<?php echo $post['id']; ?>">
                                        <button type="submit" name="delete_post" class="btn btn-danger btn-sm">Excluir</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>

            <!-- Gerenciamento de Serviços -->
            <div class="post-card p-4 mb-6">
                <h3 class="text-xl font-bold mb-4">Serviços</h3>
                <table class="table w-full">
                    <thead>
                        <tr>
                            <th>Autor</th>
                            <th>Nome</th>
                            <th>Preço</th>
                            <th>Data</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($services as $service): ?>
                            <tr>
                                <td>@<?php echo htmlspecialchars($service['username']); ?></td>
                                <td><?php echo htmlspecialchars($service['name']); ?></td>
                                <td>R$<?php echo number_format($service['price'], 2, ',', '.'); ?></td>
                                <td><?php echo date('d/m/Y', strtotime($service['created_date'])); ?></td>
                                <td>
                                    <form method="POST" onsubmit="return confirm('Tem certeza que deseja excluir este serviço?');">
                                        <input type="hidden" name="service_id" value="<?php echo $service['id']; ?>">
                                        <button type="submit" name="delete_service" class="btn btn-danger btn-sm">Excluir</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
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