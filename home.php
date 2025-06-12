<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'home');

if (isset($_GET['theme'])) {
    $_SESSION['theme'] = $_GET['theme'] === 'dark' ? 'dark' : 'light';
}
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Rede Social Profissional</title>
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
        .dark .navbar, .dark .post-card, .dark .form-control, .dark .form-select, .dark .bottom-nav {
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
            padding-bottom: 60px; /* Espaço para a barra inferior fixa */
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
        .post-card, .benefit-card {
            border: 1px solid #ffffff;
            background-color: var(--light-card);
            margin-bottom: 20px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        .profile-pic {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
        }
        .post-media {
            max-height: 500px;
            width: 100%;
            object-fit: contain;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid #ffffff;
        }
        .action-btn {
            transition: all 0.2s;
        }
        .action-btn:hover {
            transform: scale(1.1);
        }
        .trending-card {
            transition: transform 0.3s;
        }
        .trending-card:hover {
            transform: translateY(-5px);
        }
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .hero-section {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #ffffff;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
        }
        .suggestion-box {
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            background-color: white;
            border: 1px solid #ccc;
            z-index: 1000;
            padding: 5px 10px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            width: 100%;
        }
        .bottom-nav {
            background-color: var(--light-card);
            border-top: 1px solid var(--light-border);
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        .dark .bottom-nav {
            background-color: var(--dark-card);
            border-top: 1px solid var(--dark-border);
        }
        /* Resoluções menores que 1024px tratadas como móveis */
        @media (max-width: 1024px) {
            .navbar {
                display: none !important;
            }
            .bottom-nav {
                display: flex !important;
            }
            .container {
                margin-top: 0 !important; /* Remove margem superior em dispositivos móveis */
            }
        }
        /* Resoluções maiores que 1024px tratadas como desktop */
        @media (min-width: 1025px) {
            .bottom-nav {
                display: none !important;
            }
            <?php if (!isset($_SESSION['user_id'])): ?>
                .navbar {
                    display: none !important;
                }
            <?php endif; ?>
        }
    </style>
</head>
<body>
    <?php if (isset($_SESSION['user_id'])): ?>
        <nav class="navbar navbar-expand-lg fixed-top">
            <div class="container-fluid">
                <a class="navbar-brand font-bold text-xl" href="?route=home">Evoluir</a>
                <div class="navbar-nav flex-row">
                    <form class="d-flex mx-auto search-form" method="GET" action="?route=search">
                        <input type="hidden" name="route" value="search">
                        <input id="searchInput" class="form-control rounded-full w-64" type="text" name="query" placeholder="Pesquisar perfis..." aria-label="Search" autocomplete="off">
                        <div id="searchResults" class="suggestion-box" style="display: none;"></div>
                    </form>
                    <a class="nav-link px-3" href="?route=feed"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg></a>
                    <a class="nav-link px-3" href="?route=profile"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg></a>
                    <a class="nav-link px-3" href="?route=marketplace"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg></a>
                    <a class="nav-link px-3" href="?route=freelancer"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg></a>
                    <a class="nav-link px-3" href="?route=chat"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg></a>
                    <?php if (isset($_SESSION['is_admin']) && $_SESSION['is_admin']): ?>
                        <a class="nav-link px-3" href="?route=admin"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path></svg></a>
                    <?php endif; ?>
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
    <?php else: ?>
        <div class="hero-section p-8 mb-8 text-center">
            <h1 class="text-4xl font-bold mb-4">Bem-vindo ao Evoluir</h1>
            <p class="text-xl mb-6">A rede social que vai transformar sua vida financeira e profissional</p>
            <div class="flex justify-center gap-4">
                <a href="?route=register" class="btn btn-light px-6 py-3 font-bold">Comece Agora</a>
                <a href="?route=login" class="btn btn-outline-light px-6 py-3">Login</a>
            </div>
        </div>
    <?php endif; ?>

    <div class="container mx-auto mt-16 px-4 flex-grow">
        <div class="max-w-6xl mx-auto">
            <!-- Benefits Section -->
            <div id="benefits" class="mb-12">
                <h2 class="text-2xl font-bold mb-6 text-center">Por que usar o Evoluir?</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="benefit-card post-card p-6 text-center">
                        <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 class="text-xl font-bold mb-2">Educação Financeira</h3>
                        <p>Aprenda a gerenciar seu dinheiro, investir e alcançar sua independência financeira.</p>
                    </div>
                    <div class="benefit-card post-card p-6 text-center">
                        <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
                        </svg>
                        <h3 class="text-xl font-bold mb-2">Marketplace</h3>
                        <p>Venda seus produtos ou serviços sem taxas abusivas e alcance novos clientes.</p>
                    </div>
                    <div class="benefit-card post-card p-6 text-center">
                        <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                        </svg>
                        <h3 class="text-xl font-bold mb-2">Networking</h3>
                        <p>Conecte-se com profissionais e empreendedores que podem impulsionar sua carreira.</p>
                    </div>
                </div>
            </div>
            
            <!-- Public Content Section -->
            <div class="flex flex-col md:flex-row gap-6">
                <div class="w-full md:w-2/3">
                    <h3 class="text-xl font-bold mb-4">Conteúdo em Destaque</h3>
                    <?php
                    $stmt = $pdo->query("SELECT p.*, u.username, u.profile_picture FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.like_count DESC, p.created_at DESC LIMIT 5");
                    $posts = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    if (count($posts) > 0):
                        foreach ($posts as $post):
                    ?>
                            <div class="post-card p-4 mb-4">
                                <div class="flex items-center mb-3">
                                    <img src="<?php echo $post['profile_picture'] ?: generateDefaultAvatar('male'); ?>" class="profile-pic mr-3" alt="Profile Picture">
                                    <a href="?route=profile&user_id=<?php echo $post['user_id']; ?>" class="font-bold">@<?php echo htmlspecialchars($post['username']); ?></a>
                                    <span class="text-sm text-gray-500 ml-2"><?php echo date('d/m/Y', strtotime($post['created_at'])); ?></span>
                                </div>
                                <p class="mb-3"><?php echo htmlspecialchars($post['content']); ?></p>
                                <?php if ($post['media_url']): ?>
                                    <?php if ($post['media_type'] === 'image'): ?>
                                        <img src="<?php echo $post['media_url']; ?>" class="post-media" alt="Post Image">
                                    <?php elseif ($post['media_type'] === 'video'): ?>
                                        <video controls class="post-media">
                                            <source src="<?php echo $post['media_url']; ?>" type="video/mp4">
                                            Seu navegador não suporta o elemento de vídeo.
                                        </video>
                                    <?php endif; ?>
                                <?php endif; ?>
                                <div class="flex items-center text-sm text-gray-500">
                                    <span class="mr-3"><?php echo $post['like_count']; ?> curtidas</span>
                                    <span><?php echo $post['category'] ? '#' . htmlspecialchars($post['category']) : ''; ?></span>
                                </div>
                                <?php if (!isset($_SESSION['user_id'])): ?>
                                    <div class="mt-4 text-center">
                                        <p class="text-sm mb-2">Faça login para interagir com esta publicação</p>
                                        <div class="flex justify-center gap-2">
                                            <a href="?route=login" class="btn btn-primary btn-sm">Login</a>
                                            <a href="?route=register" class="btn btn-outline-primary btn-sm">Cadastrar</a>
                                        </div>
                                    </div>
                                <?php endif; ?>
                            </div>
                        <?php
                        endforeach;
                    else:
                        ?>
                        <div class="post-card p-6 text-center">
                            <p>Ainda não há publicações. Seja o primeiro a postar!</p>
                            <?php if (isset($_SESSION['user_id'])): ?>
                                <a href="?route=feed" class="btn btn-primary mt-3">Criar publicação</a>
                            <?php endif; ?>
                        </div>
                    <?php endif; ?>
                </div>
                
                <div class="w-full md:w-1/3">
                    <!-- Marketplace Preview -->
                    <div class="post-card p-4 mb-4">
                        <h3 class="font-bold mb-3">Serviços em Destaque</h3>
                        <?php
                        $stmt = $pdo->query("SELECT s.*, u.username FROM services s JOIN users u ON s.user_id = u.id WHERE s.is_active = 1 ORDER BY s.id DESC LIMIT 3");
                        $services = $stmt->fetchAll(PDO::FETCH_ASSOC);
                        foreach ($services as $service):
                        ?>
                            <div class="mb-4 pb-4 border-b last:border-b-0">
                                <h5 class="font-bold"><?php echo htmlspecialchars($service['name']); ?></h5>
                                <p class="text-sm text-gray-500 mb-1"><?php echo htmlspecialchars(substr($service['description'], 0, 50)); ?>...</p>
                                <div class="flex justify-between items-center">
                                    <span class="font-bold">R$<?php echo number_format($service['price'], 2, ',', '.'); ?></span>
                                    <?php if (isset($_SESSION['user_id'])): ?>
                                        <a href="?route=chat&user_id=<?php echo $service['user_id']; ?>" class="btn btn-primary btn-xs">Contatar</a>
                                    <?php else: ?>
                                        <a href="?route=login" class="btn btn-outline-primary btn-xs">Entrar</a>
                                    <?php endif; ?>
                                </div>
                            </div>
                        <?php endforeach; ?>
                        <a href="?route=marketplace" class="text-blue-600 text-sm">Ver todos os serviços</a>
                    </div>
                    
                    <!-- Trending Topics -->
                    <div class="post-card p-4">
                        <h3 class="font-bold mb-3">Trending Topics</h3>
                        <div class="space-y-2">
                            <a href="?route=feed&category=educacaofinanceira" class="block hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded">#educacaofinanceira</a>
                            <a href="?route=feed&category=empreendedorismo" class="block hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded">#empreendedorismo</a>
                            <a href="?route=feed&category=marketingdigital" class="block hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded">#marketingdigital</a>
                            <a href="?route=feed&category=freelancer" class="block hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded">#freelancer</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <?php if (isset($_SESSION['user_id'])): ?>
    <nav class="bottom-nav flex justify-around py-2">
        <a href="?route=search" class="text-center"><img src="https://cdn-icons-png.flaticon.com/512/622/622669.png" alt="Pesquisar" width="24" /></a>
        <a href="?route=feed" class="text-center"><img src="https://cdn-icons-png.flaticon.com/512/1946/1946436.png" alt="Home" width="24" /></a>
        <a href="?route=videos" class="text-center"><img src="https://cdn-icons-png.flaticon.com/512/727/727245.png" alt="Vídeos" width="24" /></a>
        <a href="?route=marketplace" class="text-center"><img src="https://cdn-icons-png.flaticon.com/512/2989/2989843.png" alt="Marketplace" width="24" /></a>
        <a href="?route=freelancer" class="text-center"><img src="https://cdn-icons-png.flaticon.com/512/1055/1055646.png" alt="Freelancer" width="24" /></a>
        <a href="?route=profile" class="text-center"><img src="<?php echo isset($_SESSION['profile_picture']) ? $_SESSION['profile_picture'] : 'https://cdn-icons-png.flaticon.com/512/149/149071.png'; ?>" alt="Perfil" width="24" class="rounded-full" /></a>
    </nav>
    <?php endif; ?>

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

            const searchInput = document.getElementById('searchInput');
            const searchResults = document.getElementById('searchResults');
            if (searchInput && searchResults) {
                let debounceTimeout;
                searchInput.addEventListener('input', () => {
                    clearTimeout(debounceTimeout);
                    const query = searchInput.value.trim();
                    if (query.length === 0) {
                        searchResults.style.display = 'none';
                        searchResults.innerHTML = '';
                        return;
                    }

                    debounceTimeout = setTimeout(() => {
                        fetch(`search.php?query=${encodeURIComponent(query)}`)
                            .then(res => res.json())
                            .then(data => {
                                searchResults.innerHTML = '';
                                searchResults.style.display = data.length > 0 ? 'block' : 'none';
                                if (data.length === 0) {
                                    searchResults.innerHTML = '<div class="list-group-item">Nenhum perfil encontrado.</div>';
                                    return;
                                }
                                data.forEach(user => {
                                    const avatar = user.profile_picture || 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png';
                                    const div = document.createElement('a');
                                    div.href = `?route=profile&user_id=${user.id}`;
                                    div.className = 'list-group-item list-group-item-action d-flex align-items-center gap-2';
                                    div.innerHTML = `
                                        <img src="${avatar}" width="32" height="32" style="border-radius:50%;">
                                        <span>@${user.username}</span>
                                    `;
                                    searchResults.appendChild(div);
                                });
                            })
                            .catch(err => {
                                console.error('Erro na busca:', err);
                                searchResults.style.display = 'none';
                                searchResults.innerHTML = '<div class="list-group-item">Erro ao buscar.</div>';
                            });
                    }, 300); // Debounce de 300ms para evitar múltiplas requisições
                });

                document.addEventListener('click', (e) => {
                    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                        searchResults.style.display = 'none';
                        searchResults.innerHTML = '';
                    }
                });
            }
        });
    </script>
</body>
</html>