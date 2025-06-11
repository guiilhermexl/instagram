<?php
session_start();

// Diretórios para armazenamento
define('DATA_DIR', __DIR__ . '/data/');
define('UPLOADS_DIR', __DIR__ . '/uploads/');
define('PROFILES_DIR', UPLOADS_DIR . 'profiles/');
define('POSTS_DIR', UPLOADS_DIR . 'posts/');

// Cria diretórios se não existirem
foreach ([DATA_DIR, UPLOADS_DIR, PROFILES_DIR, POSTS_DIR] as $dir) {
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
}

// Arquivos JSON
$json_files = [
    'users' => DATA_DIR . 'users.json',
    'posts' => DATA_DIR . 'posts.json',
    'comments' => DATA_DIR . 'comments.json',
    'follows' => DATA_DIR . 'follows.json',
    'messages' => DATA_DIR . 'messages.json',
    'services' => DATA_DIR . 'services.json',
    'likes' => DATA_DIR . 'likes.json',
    'visits' => DATA_DIR . 'visits.json'
];

// Inicializa arquivos JSON se não existirem
foreach ($json_files as $file) {
    if (!file_exists($file)) {
        file_put_contents($file, json_encode([]), LOCK_EX);
    }
}

// Funções para manipulação de arquivos JSON
function read_json($file) {
    if (!file_exists($file)) return [];
    $handle = fopen($file, 'r');
    flock($handle, LOCK_SH);
    $data = json_decode(file_get_contents($file), true);
    flock($handle, LOCK_UN);
    fclose($handle);
    return $data ?: [];
}

function write_json($file, $data) {
    $handle = fopen($file, 'w');
    flock($handle, LOCK_EX);
    fwrite($handle, json_encode($data, JSON_PRETTY_PRINT));
    flock($handle, LOCK_UN);
    fclose($handle);
}

// Track page visits
function logVisit($page) {
    global $json_files;
    $visits = read_json($json_files['visits']);
    $visits[] = [
        'user_id' => isset($_SESSION['user_id']) ? $_SESSION['user_id'] : null,
        'page' => $page,
        'ip_address' => $_SERVER['REMOTE_ADDR'],
        'user_agent' => $_SERVER['HTTP_USER_AGENT'],
        'visit_time' => date('Y-m-d H:i:s')
    ];
    write_json($json_files['visits'], $visits);
}

// Generate default avatar based on gender
function generateDefaultAvatar($gender) {
    return $gender === 'female' ?
        'https://cdn-icons-png.flaticon.com/512/4140/4140047.png' :
        'https://cdn-icons-png.flaticon.com/512/4140/4140048.png';
}

// Routing
$route = isset($_GET['route']) ? $_GET['route'] : 'home';
logVisit($route);

// Authentication check for restricted routes
$restricted_routes = ['post', 'service', 'message', 'update_profile', 'follow', 'unfollow', 'comment', 'profile', 'marketplace', 'chat', 'like', 'unlike'];
if (in_array($route, $restricted_routes) && !isset($_SESSION['user_id'])) {
    header("Location: ?route=login");
    exit;
}

// Handle form submissions and actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $users = read_json($json_files['users']);
    $posts = read_json($json_files['posts']);
    $comments = read_json($json_files['comments']);
    $follows = read_json($json_files['follows']);
    $messages = read_json($json_files['messages']);
    $services = read_json($json_files['services']);
    $likes = read_json($json_files['likes']);

    if ($route === 'register') {
        $full_name = filter_input(INPUT_POST, 'full_name', FILTER_SANITIZE_STRING);
        $username = filter_input(INPUT_POST, 'username', FILTER_SANITIZE_STRING);
        $email = filter_input(INPUT_POST, 'email', FILTER_SANITIZE_EMAIL);
        $password = password_hash($_POST['password'], PASSWORD_BCRYPT);
        $birth_date = filter_input(INPUT_POST, 'birth_date', FILTER_SANITIZE_STRING);
        $gender = filter_input(INPUT_POST, 'gender', FILTER_SANITIZE_STRING);
        $profile_picture = generateDefaultAvatar($gender);

        // Verifica duplicatas
        $username_exists = array_filter($users, fn($u) => $u['username'] === $username);
        $email_exists = array_filter($users, fn($u) => $u['email'] === $email);
        if ($username_exists || $email_exists) {
            $error = "Erro: Nome de usuário ou email já existe.";
        } else {
            $user_id = uniqid('u', true);
            $users[] = [
                'id' => $user_id,
                'full_name' => $full_name,
                'username' => $username,
                'email' => $email,
                'password' => $password,
                'birth_date' => $birth_date,
                'gender' => $gender,
                'profile_picture' => $profile_picture,
                'bio' => '',
                'interest' => '',
                'freelancer_status' => 'unavailable',
                'created_at' => date('Y-m-d H:i:s')
            ];
            write_json($json_files['users'], $users);
            header("Location: ?route=login");
            exit;
        }
    } elseif ($route === 'login') {
        $username = filter_input(INPUT_POST, 'username', FILTER_SANITIZE_STRING);
        $password = $_POST['password'];

        $user = array_filter($users, fn($u) => ($u['username'] === $username || $u['email'] === $username));
        $user = reset($user);
        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['username'] = $user['username'];
            $_SESSION['profile_picture'] = $user['profile_picture'];
            header("Location: ?route=feed");
            exit;
        } else {
            $error = "Credenciais inválidas.";
        }
    } elseif ($route === 'post' && isset($_SESSION['user_id'])) {
        $content = filter_input(INPUT_POST, 'content', FILTER_SANITIZE_STRING);
        $media_type = 'text';
        $media_url = null;

        // Extrai hashtags
        preg_match_all('/#(\w+)/', $content, $matches);
        $hashtags = $matches[1] ?? [];

        // Handle file upload
        if (isset($_FILES['media']) && $_FILES['media']['error'] === UPLOAD_ERR_OK) {
            $file_ext = pathinfo($_FILES['media']['name'], PATHINFO_EXTENSION);
            $file_name = uniqid('media_') . '.' . $file_ext;
            $file_path = POSTS_DIR . $file_name;
            if (move_uploaded_file($_FILES['media']['tmp_name'], $file_path)) {
                $media_url = 'uploads/posts/' . $file_name;
                $media_type = strpos($_FILES['media']['type'], 'image') !== false ? 'image' : 'video';
            }
        }

        $posts[] = [
            'id' => uniqid('p', true),
            'user_id' => $_SESSION['user_id'],
            'content' => $content,
            'hashtags' => $hashtags,
            'media_type' => $media_type,
            'media_url' => $media_url,
            'like_count' => 0,
            'created_at' => date('Y-m-d H:i:s')
        ];
        write_json($json_files['posts'], $posts);
        header("Location: ?route=feed");
        exit;
    } elseif ($route === 'comment' && isset($_SESSION['user_id'])) {
        $post_id = filter_input(INPUT_POST, 'post_id', FILTER_SANITIZE_STRING);
        $content = filter_input(INPUT_POST, 'content', FILTER_SANITIZE_STRING);
        $comments[] = [
            'id' => uniqid('c', true),
            'post_id' => $post_id,
            'user_id' => $_SESSION['user_id'],
            'content' => $content,
            'created_at' => date('Y-m-d H:i:s')
        ];
        write_json($json_files['comments'], $comments);
        header("Location: ?route=feed");
        exit;
    } elseif ($route === 'service' && isset($_SESSION['user_id'])) {
        $title = filter_input(INPUT_POST, 'title', FILTER_SANITIZE_STRING);
        $description = filter_input(INPUT_POST, 'description', FILTER_SANITIZE_STRING);
        $price = filter_input(INPUT_POST, 'price', FILTER_SANITIZE_NUMBER_FLOAT, FILTER_FLAG_ALLOW_FRACTION);
        $contact_link = filter_input(INPUT_POST, 'contact_link', FILTER_SANITIZE_URL);
        $services[] = [
            'id' => uniqid('s', true),
            'user_id' => $_SESSION['user_id'],
            'title' => $title,
            'description' => $description,
            'price' => $price,
            'contact_link' => $contact_link,
            'is_active' => true,
            'created_at' => date('Y-m-d H:i:s')
        ];
        write_json($json_files['services'], $services);
        header("Location: ?route=marketplace");
        exit;
    } elseif ($route === 'message' && isset($_SESSION['user_id'])) {
        $receiver_id = filter_input(INPUT_POST, 'receiver_id', FILTER_SANITIZE_STRING);
        $content = filter_input(INPUT_POST, 'content', FILTER_SANITIZE_STRING);
        $messages[] = [
            'id' => uniqid('m', true),
            'sender_id' => $_SESSION['user_id'],
            'receiver_id' => $receiver_id,
            'content' => $content,
            'is_read' => false,
            'created_at' => date('Y-m-d H:i:s')
        ];
        write_json($json_files['messages'], $messages);
        header("Location: ?route=chat&user_id=$receiver_id");
        exit;
    } elseif ($route === 'update_profile' && isset($_SESSION['user_id'])) {
        $bio = filter_input(INPUT_POST, 'bio', FILTER_SANITIZE_STRING);
        $interest = filter_input(INPUT_POST, 'interest', FILTER_SANITIZE_STRING);
        $freelancer_status = filter_input(INPUT_POST, 'freelancer_status', FILTER_SANITIZE_STRING);

        $profile_picture = null;
        if (isset($_FILES['profile_picture']) && $_FILES['profile_picture']['error'] === UPLOAD_ERR_OK) {
            $file_ext = pathinfo($_FILES['profile_picture']['name'], PATHINFO_EXTENSION);
            $file_name = 'profile_' . $_SESSION['user_id'] . '.' . $file_ext;
            $file_path = PROFILES_DIR . $file_name;
            if (move_uploaded_file($_FILES['profile_picture']['tmp_name'], $file_path)) {
                $profile_picture = 'uploads/profiles/' . $file_name;
            }
        }

        foreach ($users as &$user) {
            if ($user['id'] === $_SESSION['user_id']) {
                $user['bio'] = $bio;
                $user['interest'] = $interest;
                $user['freelancer_status'] = $freelancer_status;
                if ($profile_picture) {
                    $user['profile_picture'] = $profile_picture;
                    $_SESSION['profile_picture'] = $profile_picture;
                }
                break;
            }
        }
        write_json($json_files['users'], $users);
        header("Location: ?route=profile");
        exit;
    } elseif ($route === 'follow' && isset($_SESSION['user_id'])) {
        $followed_id = filter_input(INPUT_POST, 'followed_id', FILTER_SANITIZE_STRING);
        $follows[] = [
            'id' => uniqid('f', true),
            'follower_id' => $_SESSION['user_id'],
            'followed_id' => $followed_id,
            'created_at' => date('Y-m-d H:i:s')
        ];
        write_json($json_files['follows'], $follows);
        header("Location: ?route=profile&user_id=$followed_id");
        exit;
    } elseif ($route === 'unfollow' && isset($_SESSION['user_id'])) {
        $followed_id = filter_input(INPUT_POST, 'followed_id', FILTER_SANITIZE_STRING);
        $follows = array_filter($follows, fn($f) => !($f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $followed_id));
        write_json($json_files['follows'], array_values($follows));
        header("Location: ?route=profile&user_id=$followed_id");
        exit;
    } elseif ($route === 'like' && isset($_SESSION['user_id'])) {
        $post_id = filter_input(INPUT_POST, 'post_id', FILTER_SANITIZE_STRING);
        $likes[] = [
            'id' => uniqid('l', true),
            'post_id' => $post_id,
            'user_id' => $_SESSION['user_id'],
            'created_at' => date('Y-m-d H:i:s')
        ];
        foreach ($posts as &$post) {
            if ($post['id'] === $post_id) {
                $post['like_count'] = ($post['like_count'] ?? 0) + 1;
                break;
            }
        }
        write_json($json_files['likes'], $likes);
        write_json($json_files['posts'], $posts);
        header("Location: ?route=feed");
        exit;
    } elseif ($route === 'unlike' && isset($_SESSION['user_id'])) {
        $post_id = filter_input(INPUT_POST, 'post_id', FILTER_SANITIZE_STRING);
        $likes = array_filter($likes, fn($l) => !($l['post_id'] === $post_id && $l['user_id'] === $_SESSION['user_id']));
        foreach ($posts as &$post) {
            if ($post['id'] === $post_id) {
                $post['like_count'] = max(0, ($post['like_count'] ?? 0) - 1);
                break;
            }
        }
        write_json($json_files['likes'], array_values($likes));
        write_json($json_files['posts'], $posts);
        header("Location: ?route=feed");
        exit;
    } elseif ($route === 'logout') {
        session_destroy();
        header("Location: ?route=home");
        exit;
    }
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
            --dark-bg: #121212;
            --dark-card: #1e1e1e;
            --dark-text: #e0e0e0;
            --dark-border: #333;
            --light-text: #333;
            --light-bg: #f8f9fa;
            --light-card: #fff;
            --light-border: #e5e7eb;
        }

        .dark {
            background-color: var(--dark-bg);
            color: var(--dark-text);
        }

        .dark .navbar {
            background-color: var(--dark-card);
            border-bottom: 1px solid var(--dark-border);
        }

        .dark .navbar-nav .nav-link {
            color: var(--dark-text) !important;
        }

        .dark .post-card {
            background-color: var(--dark-card);
            border: 1px solid var(--dark-border);
            color: var(--dark-text);
        }

        .dark .form-control, .dark .form-select {
            background-color: var(--dark-card);
            border-color: var(--dark-border);
            color: var(--dark-text);
        }

        .dark .text-gray-500 {
            color: #a0a0a0 !important;
        }

        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-color: var(--light-bg);
            color: var(--light-text);
        }

        .navbar {
            background-color: var(--light-card);
            border-bottom: 1px solid var(--light-border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .post-card {
            border: 1px solid var(--light-border);
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
        }

        .post-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2px;
        }

        .post-grid-item {
            aspect-ratio: 1/1;
            overflow: hidden;
        }

        .post-grid-item img, .post-grid-item video {
            width: 100%;
            height: 100%;
            object-fit: cover;
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
        }

        .register-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 600px;
            max-width: 90%;
            z-index: 1000;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        .dark .register-container {
            background: var(--dark-card);
        }

        .dropdown-menu {
            background-color: var(--light-card);
            border: 1px solid var(--light-border);
        }

        .dark .dropdown-menu {
            background-color: var(--dark-card);
            border: 1px solid var(--dark-border);
        }

        .dropdown-item:hover {
            background-color: var(--primary);
            color: white !important;
        }

        @media (max-width: 768px) {
            .post-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand font-bold text-xl" href="?route=home">Evoluir</a>
            <?php if (isset($_SESSION['user_id'])): ?>
                <form class="d-flex mx-auto search-form" method="GET" action="?route=search">
                    <input type="hidden" name="route" value="search">
                    <input class="form-control rounded-full w-64" type="text" name="query" placeholder="Pesquisar perfis..." aria-label="Search">
                </form>
            <?php endif; ?>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="?route=home">Início</a>
                    </li>
                    <?php if (isset($_SESSION['user_id'])): ?>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=feed">Feed</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=profile">Perfil</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=marketplace">Marketplace</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=chat">Chat</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=logout">Logout</a>
                        </li>
                    <?php else: ?>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=login">Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="?route=register">Cadastrar</a>
                        </li>
                    <?php endif; ?>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mx-auto mt-16 px-4 flex-grow">
        <?php if (isset($error)): ?>
            <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>

        <?php if ($route === 'home'): ?>
            <div class="max-w-6xl mx-auto">
                <div class="hero-section p-8 mb-8 text-center">
                    <h1 class="text-4xl font-bold mb-4">Bem-vindo ao Evoluir</h1>
                    <p class="text-xl mb-6">A rede social que vai transformar sua vida financeira e profissional</p>
                    <div class="flex justify-center gap-4">
                        <a href="?route=register" class="btn btn-light px-6 py-3 font-bold">Comece Agora</a>
                        <a href="#benefits" class="btn btn-outline-light px-6 py-3">Saiba Mais</a>
                    </div>
                </div>
                <div id="benefits" class="mb-12">
                    <h2 class="text-2xl font-bold mb-6 text-center">Por que usar o Evoluir?</h2>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="post-card p-6 text-center">
                            <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <h3 class="text-xl font-bold mb-2">Educação Financeira</h3>
                            <p>Aprenda a gerenciar seu dinheiro, investir e alcançar sua independência financeira.</p>
                        </div>
                        <div class="post-card p-6 text-center">
                            <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                            </svg>
                            <h3 class="text-xl font-bold mb-2">Marketplace</h3>
                            <p>Venda seus produtos ou serviços sem taxas abusivas e alcance novos clientes.</p>
                        </div>
                        <div class="post-card p-6 text-center">
                            <svg class="w-12 h-12 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                            <h3 class="text-xl font-bold mb-2">Networking</h3>
                            <p>Conecte-se com profissionais e empreendedores que podem impulsionar sua carreira.</p>
                        </div>
                    </div>
                </div>
                <div class="flex flex-col md:flex-row gap-6">
                    <div class="w-full md:w-2/3">
                        <h3 class="text-xl font-bold mb-4">Conteúdo em Destaque</h3>
                        <?php
                        $posts = read_json($json_files['posts']);
                        $users = read_json($json_files['users']);
                        usort($posts, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                        $posts = array_slice($posts, 0, 5);
                        if (count($posts) > 0):
                            foreach ($posts as $post):
                                $user = array_filter($users, fn($u) => $u['id'] === $post['user_id']);
                                $user = reset($user);
                        ?>
                            <div class="post-card p-4 mb-4">
                                <div class="flex items-center mb-3">
                                    <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="profile-pic mr-3" alt="Profile Picture">
                                    <a href="?route=profile&user_id=<?php echo $post['user_id']; ?>" class="font-bold">@<?php echo htmlspecialchars($user['username']); ?></a>
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
                                    <span class="mr-3"><?php echo $post['like_count'] ?? 0; ?> curtidas</span>
                                    <span><?php echo implode(' ', array_map(fn($h) => '#' . $h, $post['hashtags'] ?? [])); ?></span>
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
                        <div class="post-card p-4 mb-4">
                            <h3 class="font-bold mb-3">Serviços em Destaque</h3>
                            <?php
                            $services = read_json($json_files['services']);
                            $services = array_filter($services, fn($s) => $s['is_active']);
                            usort($services, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                            $services = array_slice($services, 0, 3);
                            foreach ($services as $service):
                                $user = array_filter($users, fn($u) => $u['id'] === $service['user_id']);
                                $user = reset($user);
                            ?>
                                <div class="mb-4 pb-4 border-b last:border-b-0">
                                    <h5 class="font-bold"><?php echo htmlspecialchars($service['title']); ?></h5>
                                    <p class="text-sm text-gray-500 mb-1"><?php echo htmlspecialchars(substr($service['description'], 0, 50)); ?>...</p>
                                    <div class="flex justify-between items-center">
                                        <span class="font-bold">R$<?php echo number_format($service['price'], 2, ',', '.'); ?></span>
                                        <?php if (isset($_SESSION['user_id'])): ?>
                                            <a href="?route=chat&user_id=<?php echo $service['user_id']; ?>" class="btn btn-primary btn-xs">Contatar</a>
                                        <?php else: ?>
                                            <a href="?route=login" class="btn btn-outline-primary btn-xs">Login</a>
                                        <?php endif; ?>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                            <a href="?route=marketplace" class="text-blue-500 text-sm">Ver todos os serviços</a>
                        </div>
                        <div class="post-card p-4">
                            <h3 class="font-bold mb-3">Trending Topics</h3>
                            <div class="space-y-2">
                                <?php
                                $all_hashtags = array_merge(...array_map(fn($p) => $p['hashtags'] ?? [], $posts));
                                $all_hashtags = array_unique($all_hashtags);
                                $all_hashtags = array_slice($all_hashtags, 0, 4);
                                foreach ($all_hashtags as $hashtag):
                                ?>
                                    <a href="?route=feed&hashtag=<?php echo urlencode($hashtag); ?>" class="block hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded">#<?php echo htmlspecialchars($hashtag); ?></a>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        <?php elseif ($route === 'register'): ?>
            <div class="register-container p-6">
                <div class="text-center mb-6">
                    <h2 class="text-2xl font-bold mb-2">Crie sua conta</h2>
                    <p class="text-sm text-gray-500">Junte-se à comunidade que vai transformar sua vida financeira e profissional</p>
                </div>
                <form method="POST" action="?route=register" enctype="multipart/form-data" id="registerForm">
                    <div id="step1">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Nome Completo</label>
                            <input type="text" class="form-control w-full p-2 border rounded" name="full_name" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Nome de Usuário</label>
                            <input type="text" class="form-control w-full p-2 border rounded" name="username" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Email</label>
                            <input type="email" class="form-control w-full p-2 border rounded" name="email" required>
                        </div>
                        <button type="button" class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition" onclick="showStep(2)">Próximo</button>
                    </div>
                    <div id="step2" style="display: none;">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Senha</label>
                            <input type="password" class="form-control w-full p-2 border rounded" name="password" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Data de Nascimento</label>
                            <input type="date" class="form-control w-full p-2 border rounded" name="birth_date" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-1">Gênero</label>
                            <select class="form-select w-full p-2 border rounded" name="gender" required>
                                <option value="">Selecione</option>
                                <option value="male">Masculino</option>
                                <option value="female">Feminino</option>
                                <option value="other">Outro</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <div class="flex items-center">
                                <input type="checkbox" id="terms" name="terms" required class="mr-2">
                                <label for="terms" class="text-sm">Eu concordo com os <a href="#" class="text-blue-500">Termos de Serviço</a> e <a href="#" class="text-blue-500">Política de Privacidade</a></label>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <button type="button" class="w-full bg-gray-500 text-white p-2 rounded hover:bg-gray-600 transition" onclick="showStep(1)">Voltar</button>
                            <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition">Cadastrar</button>
                        </div>
                    </div>
                </form>
                <p class="text-center mt-4">Já tem uma conta? <a href="?route=login" class="text-blue-500">Faça login</a></p>
            </div>

        <?php elseif ($route === 'login'): ?>
            <div class="max-w-md mx-auto bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mt-8">
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

        <?php elseif ($route === 'profile'): ?>
            <?php
            $users = read_json($json_files['users']);
            $posts = read_json($json_files['posts']);
            $follows = read_json($json_files['follows']);
            $comments = read_json($json_files['comments']);
            $likes = read_json($json_files['likes']);
            $user_id = isset($_GET['user_id']) ? $_GET['user_id'] : $_SESSION['user_id'];
            $user = array_filter($users, fn($u) => $u['id'] === $user_id);
            $user = reset($user);
            if ($user):
                $followers = array_filter($follows, fn($f) => $f['followed_id'] === $user_id);
                $following = array_filter($follows, fn($f) => $f['follower_id'] === $user_id);
                $is_following = array_filter($follows, fn($f) => $f['follower_id'] === ($_SESSION['user_id'] ?? '') && $f['followed_id'] === $user_id);
            ?>
                <div class="max-w-4xl mx-auto">
                    <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm mb-6">
                        <div class="flex flex-col md:flex-row items-center md:items-start">
                            <div class="relative mb-4 md:mb-0 md:mr-6">
                                <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="w-24 h-24 rounded-full object-cover">
                                <?php if ($user_id == $_SESSION['user_id']): ?>
                                    <label for="profile-picture-upload" class="absolute bottom-0 right-0 bg-blue-500 text-white rounded-full p-1 cursor-pointer">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        </svg>
                                    </label>
                                <?php endif; ?>
                            </div>
                            <div class="text-center md:text-left flex-grow">
                                <h2 class="text-xl font-bold"><?php echo htmlspecialchars($user['full_name']); ?></h2>
                                <p class="text-gray-500 mb-2">@<?php echo htmlspecialchars($user['username']); ?></p>
                                <p class="mb-3"><?php echo htmlspecialchars($user['bio'] ?? 'Nenhuma bio'); ?></p>
                                <div class="flex justify-center md:justify-start space-x-4 mb-3">
                                    <a href="?route=followers&user_id=<?php echo $user_id; ?>" class="cursor-pointer"><strong><?php echo count($followers); ?></strong> seguidores</a>
                                    <a href="?route=following&user_id=<?php echo $user_id; ?>" class="cursor-pointer"><strong><?php echo count($following); ?></strong> seguindo</a>
                                </div>
                                <?php if ($user_id != $_SESSION['user_id']): ?>
                                    <div class="flex space-x-2 justify-center md:justify-start">
                                        <form method="POST" action="?route=<?php echo $is_following ? 'unfollow' : 'follow'; ?>" class="d-inline">
                                            <input type="hidden" name="followed_id" value="<?php echo $user_id; ?>">
                                            <button type="submit" class="btn btn-<?php echo $is_following ? 'outline-secondary' : 'primary'; ?> btn-sm"><?php echo $is_following ? 'Seguindo' : 'Seguir'; ?></button>
                                        </form>
                                        <a href="?route=chat&user_id=<?php echo $user_id; ?>" class="btn btn-outline-primary btn-sm">Mensagem</a>
                                    </div>
                                <?php else: ?>
                                    <button class="btn btn-outline-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#editProfileModal">Editar Perfil</button>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Publicações</h3>
                    <div class="post-grid">
                        <?php
                        $user_posts = array_filter($posts, fn($p) => $p['user_id'] === $user_id);
                        usort($user_posts, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                        foreach ($user_posts as $post):
                        ?>
                            <div class="post-grid-item">
                                <a href="?route=post_view&post_id=<?php echo $post['id']; ?>">
                                    <?php if ($post['media_type'] === 'image' && $post['media_url']): ?>
                                        <img src="<?php echo $post['media_url']; ?>" alt="Post Image">
                                    <?php elseif ($post['media_type'] === 'video' && $post['media_url']): ?>
                                        <video>
                                            <source src="<?php echo $post['media_url']; ?>" type="video/mp4">
                                        </video>
                                    <?php else: ?>
                                        <div class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                                            <p class="text-center p-2"><?php echo substr(htmlspecialchars($post['content']), 0, 50); ?>...</p>
                                        </div>
                                    <?php endif; ?>
                                </a>
                            </div>
                        <?php endforeach; ?>
                        <?php if (count($user_posts) === 0): ?>
                            <div class="col-span-3 text-center py-6">
                                <p>Nenhuma publicação ainda.</p>
                                <?php if ($user_id == $_SESSION['user_id']): ?>
                                    <a href="?route=feed" class="btn btn-primary mt-3">Criar primeira publicação</a>
                                <?php endif; ?>
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
                <div class="modal fade" id="editProfileModal" tabindex="-1" aria-labelledby="editProfileModalLabel" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="editProfileModalLabel">Editar Perfil</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form method="POST" action="?route=update_profile" enctype="multipart/form-data">
                                    <div class="mb-3 text-center">
                                        <label for="profile-picture-upload" class="cursor-pointer">
                                            <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="w-24 h-24 rounded-full mx-auto mb-2 object-cover">
                                            <span class="text-blue-500 text-sm">Alterar foto</span>
                                        </label>
                                        <input type="file" id="profile-picture-upload" name="profile_picture" class="hidden" accept="image/*">
                                    </div>
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Bio (máx. 160 caracteres)</label>
                                        <textarea class="form-control w-full p-2 border rounded" name="bio" maxlength="160"><?php echo htmlspecialchars($user['bio'] ?? ''); ?></textarea>
                                    </div>
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Interesse</label>
                                        <input type="text" class="form-control w-full p-2 border rounded" name="interest" value="<?php echo htmlspecialchars($user['interest'] ?? ''); ?>">
                                    </div>
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Status Freelancer</label>
                                        <select class="form-select w-full p-2 border rounded" name="freelancer_status">
                                            <option value="available" <?php echo $user['freelancer_status'] === 'available' ? 'selected' : ''; ?>>Disponível</option>
                                            <option value="unavailable" <?php echo $user['freelancer_status'] === 'unavailable' ? 'selected' : ''; ?>>Indisponível</option>
                                        </select>
                                    </div>
                                    <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition">Salvar</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            <?php else: ?>
                <div class="text-center py-10">
                    <h2 class="text-2xl font-bold">Usuário não encontrado</h2>
                    <a href="?route=home" class="btn btn-primary mt-4">Voltar</a>
                </div>
            <?php endif; ?>

        <?php elseif ($route === 'followers' || $route === 'following'): ?>
            <?php
            $users = read_json($json_files['users']);
            $follows = read_json($json_files['follows']);
            $user_id = isset($_GET['user_id']) ? $_GET['user_id'] : $_SESSION['user_id'];
            $user = array_filter($users, fn($u) => $u['id'] === $user_id);
            $user = reset($user);
            if ($user):
                $list = $route === 'followers' ?
                    array_filter($follows, fn($f) => $f['followed_id'] === $user_id) :
                    array_filter($follows, fn($f) => $f['follower_id'] === $user_id);
                $title = $route === 'followers' ? 'Seguidores' : 'Seguindo';
            ?>
                <div class="max-w-2xl mx-auto">
                    <h2 class="text-2xl font-bold mb-4"><?php echo $title; ?> de @<?php echo htmlspecialchars($user['username']); ?></h2>
                    <?php
                    foreach ($list as $item):
                        $target_id = $route === 'followers' ? $item['follower_id'] : $item['followed_id'];
                        $target_user = array_filter($users, fn($u) => $u['id'] === $target_id);
                        $target_user = reset($target_user);
                        if ($target_user):
                    ?>
                        <div class="post-card p-4 flex items-center justify-between mb-3">
                            <div class="flex items-center">
                                <img src="<?php echo $target_user['profile_picture'] ?: generateDefaultAvatar($target_user['gender'] ?? 'male'); ?>" class="profile-pic mr-3">
                                <div>
                                    <a href="?route=profile&user_id=<?php echo $target_user['id']; ?>" class="font-bold block">@<?php echo htmlspecialchars($target_user['username']); ?></a>
                                    <span class="text-sm text-gray-500"><?php echo htmlspecialchars($target_user['full_name']); ?></span>
                                </div>
                            </div>
                            <?php if ($target_user['id'] != $_SESSION['user_id']): ?>
                                <form method="POST" action="?route=<?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $target_user['id']) ? 'unfollow' : 'follow'; ?>">
                                    <input type="hidden" name="followed_id" value="<?php echo $target_user['id']; ?>">
                                    <button type="submit" class="btn btn-<?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $target_user['id']) ? 'outline-secondary' : 'primary'; ?> btn-sm"><?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $target_user['id']) ? 'Seguindo' : 'Seguir'; ?></button>
                                </form>
                            <?php endif; ?>
                        </div>
                    <?php
                        endif;
                    endforeach;
                    if (count($list) === 0):
                    ?>
                        <div class="post-card p-6 text-center">
                            <p>Nenhum <?php echo strtolower($title); ?> encontrado.</p>
                        </div>
                    <?php endif; ?>
                </div>
            <?php else: ?>
                <div class="text-center py-10">
                    <h2 class="text-2xl font-bold">Usuário não encontrado</h2>
                    <a href="?route=home" class="btn btn-primary mt-4">Voltar</a>
                </div>
            <?php endif; ?>

        <?php elseif ($route === 'post_view'): ?>
            <?php
            $posts = read_json($json_files['posts']);
            $users = read_json($json_files['users']);
            $comments = read_json($json_files['comments']);
            $likes = read_json($json_files['likes']);
            $post_id = $_GET['post_id'] ?? '';
            $post = array_filter($posts, fn($p) => $p['id'] === $post_id);
            $post = reset($post);
            if ($post):
                $user = array_filter($users, fn($u) => $u['id'] === $post['user_id']);
                $user = reset($user);
                $post_comments = array_filter($comments, fn($c) => $c['post_id'] === $post_id);
                $like_count = count(array_filter($likes, fn($l) => $l['post_id'] === $post_id));
                $user_like = array_filter($likes, fn($l) => $l['post_id'] === $post_id && $l['user_id'] === ($_SESSION['user_id'] ?? ''));
                $post_url = urlencode("http://$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]");
            ?>
                <div class="max-w-2xl mx-auto">
                    <div class="post-card p-4 mb-6">
                        <div class="flex items-center mb-3">
                            <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="profile-pic mr-3" alt="Profile Picture">
                            <div class="flex-grow">
                                <a href="?route=profile&user_id=<?php echo $post['user_id']; ?>" class="font-bold">@<?php echo htmlspecialchars($user['username']); ?></a>
                                <p class="text-sm text-gray-500"><?php echo date('d/m/Y H:i', strtotime($post['created_at'])); ?></p>
                            </div>
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
                        <div class="flex items-center justify-between text-sm text-gray-500 mb-3">
                            <div class="flex items-center space-x-4">
                                <form method="POST" action="?route=<?php echo $user_like ? 'unlike' : 'like'; ?>" class="d-inline">
                                    <input type="hidden" name="post_id" value="<?php echo $post['id']; ?>">
                                    <button type="submit" class="flex items-center">
                                        <svg class="w-5 h-5 <?php echo $user_like ? 'text-red-500 fill-current' : 'text-gray-500'; ?>" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                        </svg>
                                        <span class="ml-1"><?php echo $like_count; ?></span>
                                    </button>
                                </form>
                                <button class="flex items-center">
                                    <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                                    </svg>
                                    <span class="ml-1"><?php echo count($post_comments); ?></span>
                                </button>
                            </div>
                            <span class="text-blue-500"><?php echo implode(' ', array_map(fn($h) => '#' . $h, $post['hashtags'] ?? [])); ?></span>
                        </div>
                        <div class="flex space-x-2 mb-3">
                            <a href="https://twitter.com/intent/tweet?url=<?php echo $post_url; ?>&text=Confira%20esta%20publicação%20no%20Evoluir!" class="btn btn-outline-primary btn-sm">Twitter</a>
                            <a href="https://api.whatsapp.com/send?text=Confira%20esta%20publicação%20no%20Evoluir!%20<?php echo $post_url; ?>" class="btn btn-outline-primary btn-sm">WhatsApp</a>
                            <a href="https://www.facebook.com/sharer/sharer.php?u=<?php echo $post_url; ?>" class="btn btn-outline-primary btn-sm">Facebook</a>
                            <button onclick="copyLink('<?php echo $post_url; ?>')" class="btn btn-outline-primary btn-sm">Copiar Link</button>
                        </div>
                        <?php if (isset($_SESSION['user_id'])): ?>
                            <form method="POST" action="?route=comment" class="mb-3">
                                <input type="hidden" name="post_id" value="<?php echo $post['id']; ?>">
                                <div class="flex">
                                    <input type="text" class="form-control flex-grow p-2 border rounded-l" name="content" placeholder="Adicionar comentário..." required>
                                    <button type="submit" class="bg-blue-500 text-white p-2 rounded-r">Enviar</button>
                                </div>
                            </form>
                        <?php endif; ?>
                        <?php
                        usort($post_comments, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                        $post_comments = array_slice($post_comments, 0, 3);
                        foreach ($post_comments as $comment):
                            $comment_user = array_filter($users, fn($u) => $u['id'] === $comment['user_id']);
                            $comment_user = reset($comment_user);
                        ?>
                            <div class="flex items-start mb-2">
                                <img src="<?php echo $comment_user['profile_picture'] ?: generateDefaultAvatar($comment_user['gender'] ?? 'male'); ?>" class="rounded-full w-6 h-6 mt-1 mr-2">
                                <div>
                                    <span class="font-bold text-sm">@<?php echo htmlspecialchars($comment_user['username']); ?></span>
                                    <span class="text-sm"><?php echo htmlspecialchars($comment['content']); ?></span>
                                </div>
                            </div>
                        <?php endforeach; ?>
                        <?php if (count($post_comments) > 0): ?>
                            <a href="#" class="text-sm text-gray-500">Ver todos os comentários</a>
                        <?php endif; ?>
                    </div>
                </div>
            <?php else: ?>
                <div class="text-center py-10">
                    <h2 class="text-2xl font-bold">Publicação não encontrada</h2>
                    <a href="?route=feed" class="btn btn-primary mt-4">Voltar</a>
                </div>
            <?php endif; ?>

        <?php elseif ($route === 'feed'): ?>
            <div class="max-w-2xl mx-auto">
                <?php if (isset($_SESSION['user_id'])): ?>
                    <div class="post-card p-4 mb-6">
                        <form method="POST" action="?route=post" enctype="multipart/form-data">
                            <div class="flex items-center mb-3">
                                <img src="<?php echo $_SESSION['profile_picture'] ?? generateDefaultAvatar('male'); ?>" class="profile-pic mr-3">
                                <span class="font-bold">@<?php echo htmlspecialchars($_SESSION['username']); ?></span>
                            </div>
                            <div class="mb-3">
                                <textarea class="form-control w-full p-3 border rounded" name="content" maxlength="500" placeholder="No que você está pensando? Use # para hashtags" rows="3" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="block text-sm font-medium mb-1">Mídia (opcional)</label>
                                <input type="file" class="form-control w-full p-2 border rounded" name="media" accept="image/*,video/*">
                            </div>
                            <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition">Postar</button>
                        </form>
                    </div>
                <?php endif; ?>
                <?php
                $posts = read_json($json_files['posts']);
                $users = read_json($json_files['users']);
                $comments = read_json($json_files['comments']);
                $likes = read_json($json_files['likes']);
                $follows = read_json($json_files['follows']);
                $hashtag = isset($_GET['hashtag']) ? filter_input(INPUT_GET, 'hashtag', FILTER_SANITIZE_STRING) : '';
                if ($hashtag) {
                    $posts = array_filter($posts, fn($p) => in_array($hashtag, $p['hashtags'] ?? []));
                }
                usort($posts, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                if (count($posts) < 2) {
                    $posts = array_merge($posts, [
                        [
                            'id' => 'example1',
                            'user_id' => 'example_user',
                            'content' => 'Bem-vindo ao Evoluir! Esta é uma postagem de exemplo. #educacaofinanceira',
                            'hashtags' => ['educacaofinanceira'],
                            'media_type' => 'text',
                            'media_url' => null,
                            'like_count' => 10,
                            'created_at' => date('Y-m-d H:i:s', strtotime('-1 day'))
                        ],
                        [
                            'id' => 'example2',
                            'user_id' => 'example_user',
                            'content' => 'Aprenda a investir com nossas dicas! #investimento',
                            'hashtags' => ['investimento'],
                            'media_type' => 'text',
                            'media_url' => null,
                            'like_count' => 5,
                            'created_at' => date('Y-m-d H:i:s', strtotime('-2 days'))
                        ]
                    ]);
                }
                $posts = array_slice($posts, 0, 5);
                foreach ($posts as $post):
                    $user = array_filter($users, fn($u) => $u['id'] === $post['user_id']);
                    $user = reset($user) ?: ['username' => 'Exemplo', 'profile_picture' => generateDefaultAvatar('male'), 'gender' => 'male'];
                    $is_following = array_filter($follows, fn($f) => $f['follower_id'] === ($_SESSION['user_id'] ?? '') && $f['followed_id'] === $post['user_id']);
                    $post_comments = array_filter($comments, fn($c) => $c['post_id'] === $post['id']);
                    $like_count = count(array_filter($likes, fn($l) => $l['post_id'] === $post['id']));
                    $user_like = array_filter($likes, fn($l) => $l['post_id'] === $post['id'] && $l['user_id'] === ($_SESSION['user_id'] ?? ''));
                    $post_url = urlencode("http://$_SERVER[HTTP_HOST]?route=post_view&post_id=" . $post['id']);
                ?>
                    <div class="post-card p-4 mb-6">
                        <div class="flex items-center mb-3">
                            <img src="<?php echo $user['profile_picture']; ?>" class="profile-pic mr-3" alt="Profile Picture">
                            <div class="flex-grow">
                                <a href="?route=profile&user_id=<?php echo $post['user_id']; ?>" class="font-bold">@<?php echo htmlspecialchars($user['username']); ?></a>
                                <p class="text-sm text-gray-500"><?php echo date('d/m/Y H:i', strtotime($post['created_at'])); ?></p>
                            </div>
                            <?php if (isset($_SESSION['user_id']) && $post['user_id'] != $_SESSION['user_id'] && $post['user_id'] != 'example_user'): ?>
                                <form method="POST" action="?route=<?php echo $is_following ? 'unfollow' : 'follow'; ?>">
                                    <input type="hidden" name="followed_id" value="<?php echo $post['user_id']; ?>">
                                    <button type="submit" class="btn btn-<?php echo $is_following ? 'outline-secondary' : 'primary'; ?> btn-sm"><?php echo $is_following ? 'Seguindo' : 'Seguir'; ?></button>
                                </form>
                            <?php endif; ?>
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
                        <div class="flex items-center justify-between text-sm text-gray-500 mb-3">
                            <div class="flex items-center space-x-4">
                                <?php if (isset($_SESSION['user_id']) && $post['id'] != 'example1' && $post['id'] != 'example2'): ?>
                                    <form method="POST" action="?route=<?php echo $user_like ? 'unlike' : 'like'; ?>" class="d-inline">
                                        <input type="hidden" name="post_id" value="<?php echo $post['id']; ?>">
                                        <button type="submit" class="flex items-center">
                                            <svg class="w-5 h-5 <?php echo $user_like ? 'text-red-500 fill-current' : 'text-gray-500'; ?>" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                            </svg>
                                                                                        <span class="ml-1"><?php echo $like_count; ?></span>
                                        </button>
                                    </form>
                                <?php endif; ?>
                                <a href="?route=post_view&post_id=<?php echo $post['id']; ?>" class="flex items-center">
                                    <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                                    </svg>
                                    <span class="ml-1"><?php echo count($post_comments); ?></span>
                                </a>
                            </div>
                            <span class="text-blue-500"><?php echo implode(' ', array_map(fn($h) => '#' . $h, $post['hashtags'] ?? [])); ?></span>
                        </div>
                        <div class="flex space-x-2 mb-3">
                            <a href="https://twitter.com/intent/tweet?url=<?php echo $post_url; ?>&text=Confira%20esta%20publicação%20no%20Evoluir!" class="btn btn-outline-primary btn-sm">Twitter</a>
                            <a href="https://api.whatsapp.com/send?text=Confira%20esta%20publicação%20no%20Evoluir!%20<?php echo $post_url; ?>" class="btn btn-outline-primary btn-sm">WhatsApp</a>
                            <a href="https://www.facebook.com/sharer/sharer.php?u=<?php echo $post_url; ?>" class="btn btn-outline-primary btn-sm">Facebook</a>
                            <button onclick="copyLink('<?php echo $post_url; ?>')" class="btn btn-outline-primary btn-sm">Copiar Link</button>
                        </div>
                        <?php if (isset($_SESSION['user_id'])): ?>
                            <form method="POST" action="?route=comment" class="mb-3">
                                <input type="hidden" name="post_id" value="<?php echo $post['id']; ?>">
                                <div class="flex">
                                    <input type="text" class="form-control flex-grow p-2 border rounded-l" name="content" placeholder="Adicionar comentário..." required>
                                    <button type="submit" class="bg-blue-500 text-white p-2 rounded-r">Enviar</button>
                                </div>
                            </form>
                        <?php endif; ?>
                        <?php
                        usort($post_comments, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                        $post_comments = array_slice($post_comments, 0, 3);
                        foreach ($post_comments as $comment):
                            $comment_user = array_filter($users, fn($u) => $u['id'] === $comment['user_id']);
                            $comment_user = reset($comment_user);
                        ?>
                            <div class="flex items-start mb-2">
                                <img src="<?php echo $comment_user['profile_picture'] ?: generateDefaultAvatar($comment_user['gender'] ?? 'male'); ?>" class="rounded-full w-6 h-6 mt-1 mr-2">
                                <div>
                                    <span class="font-bold text-sm">@<?php echo htmlspecialchars($comment_user['username']); ?></span>
                                    <span class="text-sm"><?php echo htmlspecialchars($comment['content']); ?></span>
                                </div>
                            </div>
                        <?php endforeach; ?>
                        <?php if (count($post_comments) > 0): ?>
                            <a href="?route=post_view&post_id=<?php echo $post['id']; ?>" class="text-sm text-gray-500">Ver todos os comentários</a>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>

        <?php elseif ($route === 'marketplace'): ?>
            <div class="max-w-4xl mx-auto">
                <h2 class="text-2xl font-bold mb-6">Marketplace</h2>
                <?php if (isset($_SESSION['user_id'])): ?>
                    <div class="post-card p-4 mb-6">
                        <h3 class="font-bold mb-3">Oferecer um Serviço</h3>
                        <form method="POST" action="?route=service">
                            <div class="mb-3">
                                <label class="block text-sm font-medium mb-1">Título do Serviço</label>
                                <input type="text" class="form-control w-full p-2 border rounded" name="title" required>
                            </div>
                            <div class="mb-3">
                                <label class="block text-sm font-medium mb-1">Descrição</label>
                                <textarea class="form-control w-full p-2 border rounded" name="description" rows="4" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="block text-sm font-medium mb-1">Preço (R$)</label>
                                <input type="number" step="0.01" class="form-control w-full p-2 border rounded" name="price" required>
                            </div>
                            <div class="mb-3">
                                <label class="block text-sm font-medium mb-1">Link de Contato</label>
                                <input type="url" class="form-control w-full p-2 border rounded" name="contact_link" placeholder="https://..." required>
                            </div>
                            <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition">Publicar Serviço</button>
                        </form>
                    </div>
                <?php endif; ?>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <?php
                    $services = read_json($json_files['services']);
                    $users = read_json($json_files['users']);
                    $services = array_filter($services, fn($s) => $s['is_active']);
                    usort($services, fn($a, $b) => strtotime($b['created_at']) <=> strtotime($a['created_at']));
                    foreach ($services as $service):
                        $user = array_filter($users, fn($u) => $u['id'] === $service['user_id']);
                        $user = reset($user);
                    ?>
                        <div class="post-card p-4">
                            <h4 class="font-bold mb-2"><?php echo htmlspecialchars($service['title']); ?></h4>
                            <p class="text-sm text-gray-500 mb-3"><?php echo htmlspecialchars($service['description']); ?></p>
                            <div class="flex items-center mb-3">
                                <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="profile-pic mr-2">
                                <a href="?route=profile&user_id=<?php echo $service['user_id']; ?>" class="text-sm font-bold">@<?php echo htmlspecialchars($user['username']); ?></a>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="font-bold">R$<?php echo number_format($service['price'], 2, ',', '.'); ?></span>
                                <?php if (isset($_SESSION['user_id'])): ?>
                                    <a href="<?php echo $service['contact_link']; ?>" target="_blank" class="btn btn-primary btn-sm">Contatar</a>
                                <?php else: ?>
                                    <a href="?route=login" class="btn btn-outline-primary btn-sm">Login para Contatar</a>
                                <?php endif; ?>
                            </div>
                        </div>
                    <?php endforeach; ?>
                    <?php if (count($services) === 0): ?>
                        <div class="col-span-2 text-center py-6">
                            <p>Nenhum serviço disponível no momento.</p>
                            <?php if (isset($_SESSION['user_id'])): ?>
                                <a href="#" class="btn btn-primary mt-3" onclick="window.scrollTo(0,0);">Oferecer um Serviço</a>
                            <?php endif; ?>
                        </div>
                    <?php endif; ?>
                </div>
            </div>

        <?php elseif ($route === 'chat'): ?>
            <?php
            $users = read_json($json_files['users']);
            $messages = read_json($json_files['messages']);
            $receiver_id = isset($_GET['user_id']) ? filter_input(INPUT_GET, 'user_id', FILTER_SANITIZE_STRING) : null;
            $current_user = array_filter($users, fn($u) => $u['id'] === $_SESSION['user_id']);
            $current_user = reset($current_user);
            $conversations = [];
            foreach ($messages as $msg) {
                $other_id = $msg['sender_id'] === $_SESSION['user_id'] ? $msg['receiver_id'] : $msg['sender_id'];
                if (!isset($conversations[$other_id]) || strtotime($msg['created_at']) > strtotime($conversations[$other_id]['last_message']['created_at'])) {
                    $conversations[$other_id] = [
                        'user' => array_filter($users, fn($u) => $u['id'] === $other_id)[array_key_first(array_filter($users, fn($u) => $u['id'] === $other_id))] ?? null,
                        'last_message' => $msg
                    ];
                }
            }
            usort($conversations, fn($a, $b) => strtotime($b['last_message']['created_at']) <=> strtotime($a['last_message']['created_at']));
            ?>
            <div class="max-w-4xl mx-auto flex flex-col md:flex-row gap-4">
                <div class="w-full md:w-1/3 post-card p-4">
                    <h3 class="font-bold mb-3">Conversas</h3>
                    <?php foreach ($conversations as $conv): ?>
                        <?php if ($conv['user']): ?>
                            <a href="?route=chat&user_id=<?php echo $conv['user']['id']; ?>" class="flex items-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded mb-2">
                                <img src="<?php echo $conv['user']['profile_picture'] ?: generateDefaultAvatar($conv['user']['gender'] ?? 'male'); ?>" class="profile-pic mr-2">
                                <div>
                                    <span class="font-bold text-sm">@<?php echo htmlspecialchars($conv['user']['username']); ?></span>
                                    <p class="text-sm text-gray-500 truncate"><?php echo htmlspecialchars(substr($conv['last_message']['content'], 0, 30)); ?>...</p>
                                </div>
                            </a>
                        <?php endif; ?>
                    <?php endforeach; ?>
                    <?php if (count($conversations) === 0): ?>
                        <p class="text-center text-sm text-gray-500">Nenhuma conversa iniciada.</p>
                    <?php endif; ?>
                </div>
                <div class="w-full md:w-2/3 post-card p-4">
                    <?php if ($receiver_id): ?>
                        <?php
                        $receiver = array_filter($users, fn($u) => $u['id'] === $receiver_id);
                        $receiver = reset($receiver);
                        if ($receiver):
                            $chat_messages = array_filter($messages, fn($m) => (
                                ($m['sender_id'] === $_SESSION['user_id'] && $m['receiver_id'] === $receiver_id) ||
                                ($m['sender_id'] === $receiver_id && $m['receiver_id'] === $_SESSION['user_id'])
                            ));
                            usort($chat_messages, fn($a, $b) => strtotime($a['created_at']) <=> strtotime($b['created_at']));
                        ?>
                            <div class="flex items-center mb-4">
                                <img src="<?php echo $receiver['profile_picture'] ?: generateDefaultAvatar($receiver['gender'] ?? 'male'); ?>" class="profile-pic mr-2">
                                <h3 class="font-bold">@<?php echo htmlspecialchars($receiver['username']); ?></h3>
                            </div>
                            <div class="h-96 overflow-y-auto mb-4 p-4 border rounded">
                                <?php foreach ($chat_messages as $msg): ?>
                                    <div class="mb-2 <?php echo $msg['sender_id'] === $_SESSION['user_id'] ? 'text-right' : 'text-left'; ?>">
                                        <div class="inline-block p-2 rounded-lg <?php echo $msg['sender_id'] === $_SESSION['user_id'] ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-600'; ?>">
                                            <p class="text-sm"><?php echo htmlspecialchars($msg['content']); ?></p>
                                            <span class="text-xs text-gray-400"><?php echo date('d/m H:i', strtotime($msg['created_at'])); ?></span>
                                        </div>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                            <form method="POST" action="?route=message">
                                <input type="hidden" name="receiver_id" value="<?php echo $receiver_id; ?>">
                                <div class="flex">
                                    <input type="text" class="form-control flex-grow p-2 border rounded-l" name="content" placeholder="Digite sua mensagem..." required>
                                    <button type="submit" class="bg-blue-500 text-white p-2 rounded-r">Enviar</button>
                                </div>
                            </form>
                        <?php else: ?>
                            <p class="text-center py-6">Usuário não encontrado.</p>
                        <?php endif; ?>
                    <?php else: ?>
                        <p class="text-center py-6">Selecione uma conversa para começar.</p>
                    <?php endif; ?>
                </div>
            </div>

        <?php elseif ($route === 'search'): ?>
            <?php
            $query = isset($_GET['query']) ? filter_input(INPUT_GET, 'query', FILTER_SANITIZE_STRING) : '';
            $users = read_json($json_files['users']);
            $results = array_filter($users, fn($u) => stripos($u['username'], $query) !== false || stripos($u['full_name'], $query) !== false);
            ?>
            <div class="max-w-2xl mx-auto">
                <h2 class="text-2xl font-bold mb-4">Resultados da Pesquisa: "<?php echo htmlspecialchars($query); ?>"</h2>
                <?php if (count($results) > 0): ?>
                    <?php foreach ($results as $user): ?>
                        <div class="post-card p-4 flex items-center justify-between mb-3">
                            <div class="flex items-center">
                                <img src="<?php echo $user['profile_picture'] ?: generateDefaultAvatar($user['gender'] ?? 'male'); ?>" class="profile-pic mr-3">
                                <div>
                                    <a href="?route=profile&user_id=<?php echo $user['id']; ?>" class="font-bold block">@<?php echo htmlspecialchars($user['username']); ?></a>
                                    <span class="text-sm text-gray-500"><?php echo htmlspecialchars($user['full_name']); ?></span>
                                </div>
                            </div>
                            <?php if ($user['id'] != $_SESSION['user_id']): ?>
                                <form method="POST" action="?route=<?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $user['id']) ? 'unfollow' : 'follow'; ?>">
                                    <input type="hidden" name="followed_id" value="<?php echo $user['id']; ?>">
                                    <button type="submit" class="btn btn-<?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $user['id']) ? 'outline-secondary' : 'primary'; ?> btn-sm"><?php echo array_filter($follows, fn($f) => $f['follower_id'] === $_SESSION['user_id'] && $f['followed_id'] === $user['id']) ? 'Seguindo' : 'Seguir'; ?></button>
                                </form>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <div class="post-card p-6 text-center">
                        <p>Nenhum usuário encontrado para "<?php echo htmlspecialchars($query); ?>".</p>
                    </div>
                <?php endif; ?>
            </div>

        <?php endif; ?>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showStep(step) {
            document.getElementById('step1').style.display = step === 1 ? 'block' : 'none';
            document.getElementById('step2').style.display = step === 2 ? 'block' : 'none';
        }

        function toggleTheme() {
            const isDark = document.documentElement.classList.toggle('dark');
            fetch('?route=theme&mode=' + (isDark ? 'dark' : 'light'), { method: 'POST' })
                .then(() => console.log('Theme updated'));
        }

        function copyLink(url) {
            navigator.clipboard.writeText(decodeURIComponent(url))
                .then(() => alert('Link copiado para a área de transferência!'))
                .catch(() => alert('Falha ao copiar o link.'));
        }

        // Handle theme route
        <?php
        if ($route === 'theme' && isset($_GET['mode'])) {
            $mode = filter_input(INPUT_GET, 'mode', FILTER_SANITIZE_STRING);
            if (in_array($mode, ['light', 'dark'])) {
                $_SESSION['theme'] = $mode;
                header("Location: " . $_SERVER['HTTP_REFERER']);
                exit;
            }
        }
        ?>
    </script>

    <!-- Configuração para Render -->
    <!--
    # Procfile
    web: vendor/bin/heroku-php-apache2 .

    # .render.yaml
    services:
      - type: web
        name: evoluir
        env: php
        plan: free
        buildCommand: ""
        startCommand: "php -S 0.0.0.0:$PORT"
        envVars:
          - key: PHP_VERSION
            value: 8.1
        disk:
          name: data
          mountPath: /app/data
          sizeGB: 1
          writeable: true
          retentionPolicy: retain
        disk:
          name: uploads
          mountPath: /app/uploads
          sizeGB: 1
          writeable: true
          retentionPolicy: retain
    -->
</body>
</html>