<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'profile');

$user_id = isset($_GET['user_id']) ? (int)$_GET['user_id'] : $_SESSION['user_id'];
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch();

if (!$user) {
    header("Location: ?route=feed");
    exit;
}

$is_own_profile = $user_id === $_SESSION['user_id'];

// Processa seguir/deseguir
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['follow_action']) && !$is_own_profile) {
    if ($_POST['follow_action'] === 'follow') {
        $stmt = $pdo->prepare("INSERT INTO followers (follower_id, followed_id) VALUES (?, ?)");
        $stmt->execute([$_SESSION['user_id'], $user_id]);
    } elseif ($_POST['follow_action'] === 'unfollow') {
        $stmt = $pdo->prepare("DELETE FROM followers WHERE follower_id = ? AND followed_id = ?");
        $stmt->execute([$_SESSION['user_id'], $user_id]);
    }
    header("Location: ?route=profile&user_id=$user_id");
    exit;
}

// Processa atualização de perfil
if ($is_own_profile && $_SERVER['REQUEST_METHOD'] === 'POST' && !isset($_POST['follow_action'])) {
    $full_name = filter_input(INPUT_POST, 'full_name', FILTER_SANITIZE_STRING);
    $bio = filter_input(INPUT_POST, 'bio', FILTER_SANITIZE_STRING);
    
    if (isset($_FILES['profile_picture']) && $_FILES['profile_picture']['error'] === UPLOAD_ERR_OK) {
        $upload_dir = 'Uploads/profiles/';
        if (!is_dir($upload_dir)) {
            mkdir($upload_dir, 0755, true);
        }
        $file_ext = pathinfo($_FILES['profile_picture']['name'], PATHINFO_EXTENSION);
        $file_name = uniqid() . '.' . $file_ext;
        $file_path = $upload_dir . $file_name;
        if (move_uploaded_file($_FILES['profile_picture']['tmp_name'], $file_path)) {
            $stmt = $pdo->prepare("UPDATE users SET full_name = ?, bio = ?, profile_picture = ? WHERE id = ?");
            $stmt->execute([$full_name, $bio, $file_path, $_SESSION['user_id']]);
        }
    } else {
        $stmt = $pdo->prepare("UPDATE users SET full_name = ?, bio = ? WHERE id = ?");
        $stmt->execute([$full_name, $bio, $_SESSION['user_id']]);
    }
    header("Location: ?route=profile");
    exit;
}

// Verifica se o usuário atual segue o perfil
$stmt = $pdo->prepare("SELECT COUNT(*) FROM followers WHERE follower_id = ? AND followed_id = ?");
$stmt->execute([$_SESSION['user_id'], $user_id]);
$is_following = $stmt->fetchColumn() > 0;

// Conta seguidores e seguidos
$stmt = $pdo->prepare("SELECT COUNT(*) FROM followers WHERE followed_id = ?");
$stmt->execute([$user_id]);
$followers_count = $stmt->fetchColumn();

$stmt = $pdo->prepare("SELECT COUNT(*) FROM followers WHERE follower_id = ?");
$stmt->execute([$user_id]);
$following_count = $stmt->fetchColumn();

// Busca posts
$stmt = $pdo->prepare("SELECT p.*, u.username, u.profile_picture FROM posts p JOIN users u ON p.user_id = u.id WHERE p.user_id = ? ORDER BY p.created_at DESC LIMIT 5");
$stmt->execute([$user_id]);
$posts = $stmt->fetchAll();

// Busca serviços
$stmt = $pdo->prepare("SELECT * FROM services WHERE user_id = ? AND is_active = 1 LIMIT 3");
$stmt->execute([$user_id]);
$services = $stmt->fetchAll();
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Perfil de @<?php echo htmlspecialchars($user['username']); ?></title>
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
        .dark .post-card {
            background-color: var(--dark-card);
            border-color: var(--dark-border);
            color: var(--dark-text);
        }
        .dark .form-control, .dark .form-select {
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
        .profile-pic-large {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #ffffff;
        }
        .post-media {
            max-height: 500px;
            width: 100%;
            object-fit: contain;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid var(--light-border);
        }
        .dark .post-media {
            border-color: var(--dark-border);
        }
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .btn-follow {
            background-color: #28a745;
            border-color: #28a745;
            color: white;
        }
        .btn-follow:hover {
            background-color: #218838;
            border-color: #218838;
        }
        .action-btn {
            transition: all 0.2s;
        }
        .action-btn:hover {
            transform: scale(1.1);
        }
    </style>
</head>
<body>
    <div class="container mx-auto mt-16 px-4 flex-grow">
        <div class="max-w-4xl mx-auto">
            <!-- Perfil do Usuário -->
            <div class="post-card p-6 mb-6">
                <div class="flex items-center mb-4">
                    <img src="<?php echo htmlspecialchars($user['profile_picture'] ?: generateDefaultAvatar($user['gender'])); ?>" class="profile-pic-large mr-4" alt="Profile Picture">
                    <div>
                        <h2 class="text-2xl font-bold">@<?php echo htmlspecialchars($user['username']); ?></h2>
                        <p class="text-gray-500"><?php echo htmlspecialchars($user['full_name']); ?></p>
                    </div>
                </div>
                <p class="mb-4"><?php echo htmlspecialchars($user['bio'] ?: 'Nenhuma bio definida.'); ?></p>
                <div class="flex gap-4 mb-4">
                    <a href="#" class="text-sm text-blue-500" data-bs-toggle="modal" data-bs-target="#followersModal"><?php echo $followers_count; ?> seguidores</a>
                    <a href="#" class="text-sm text-blue-500" data-bs-toggle="modal" data-bs-target="#followingModal"><?php echo $following_count; ?> seguindo</a>
                </div>
                <p class="text-sm text-gray-500 mb-4">Data de Nascimento: <?php echo date('d/m/Y', strtotime($user['birth_date'])); ?> | Gênero: <?php echo ucfirst($user['gender']); ?></p>
                <div class="flex gap-2">
                    <?php if ($is_own_profile): ?>
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#editProfileModal">Editar Perfil</button>
                    <?php else: ?>
                        <form method="POST" action="?route=profile&user_id=<?php echo $user_id; ?>">
                            <input type="hidden" name="follow_action" value="<?php echo $is_following ? 'unfollow' : 'follow'; ?>">
                            <button type="submit" class="btn btn-follow"><?php echo $is_following ? 'Deixar de seguir' : 'Seguir'; ?></button>
                        </form>
                        <a href="?route=chat&user_id=<?php echo $user['id']; ?>" class="btn btn-primary">Enviar Mensagem</a>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Modal de Edição de Perfil -->
            <?php if ($is_own_profile): ?>
                <div class="modal fade" id="editProfileModal" tabindex="-1" aria-labelledby="editProfileModalLabel" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content post-card">
                            <div class="modal-header">
                                <h5 class="modal-title" id="editProfileModalLabel">Editar Perfil</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form method="POST" enctype="multipart/form-data">
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Nome Completo</label>
                                        <input type="text" class="form-control w-full p-2 border rounded" name="full_name" value="<?php echo htmlspecialchars($user['full_name']); ?>" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Bio</label>
                                        <textarea class="form-control w-full p-2 border rounded" name="bio" rows="4"><?php echo htmlspecialchars($user['bio']); ?></textarea>
                                    </div>
                                    <div class="mb-3">
                                        <label class="block text-sm font-medium mb-1">Foto de Perfil</label>
                                        <input type="file" class="form-control w-full p-2 border rounded" name="profile_picture" accept="image/*">
                                    </div>
                                    <div class="flex justify-end">
                                        <button type="submit" class="btn btn-primary px-4 py-2">Salvar</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Modal de Seguidores -->
            <div class="modal fade" id="followersModal" tabindex="-1" aria-labelledby="followersModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content post-card">
                        <div class="modal-header">
                            <h5 class="modal-title" id="followersModalLabel">Seguidores</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <?php
                            $stmt = $pdo->prepare("SELECT u.id, u.username, u.profile_picture FROM users u JOIN followers f ON u.id = f.follower_id WHERE f.followed_id = ?");
                            $stmt->execute([$user_id]);
                            $followers = $stmt->fetchAll();
                            if (count($followers) > 0): ?>
                                <?php foreach ($followers as $follower): ?>
                                    <div class="flex items-center p-2 mb-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                                        <img src="<?php echo htmlspecialchars($follower['profile_picture'] ?: generateDefaultAvatar('male')); ?>" alt="Profile Picture" class="profile-pic mr-2">
                                        <a href="?route=profile&user_id=<?php echo $follower['id']; ?>" class="text-sm">@<?php echo htmlspecialchars($follower['username']); ?></a>
                                    </div>
                                <?php endforeach; ?>
                            <?php else: ?>
                                <p class="text-sm">Nenhum seguidor.</p>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal de Seguindo -->
            <div class="modal fade" id="followingModal" tabindex="-1" aria-labelledby="followingModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content post-card">
                        <div class="modal-header">
                            <h5 class="modal-title" id="followingModalLabel">Seguindo</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <?php
                            $stmt = $pdo->prepare("SELECT u.id, u.username, u.profile_picture FROM users u JOIN followers f ON u.id = f.followed_id WHERE f.follower_id = ?");
                            $stmt->execute([$user_id]);
                            $following = $stmt->fetchAll();
                            if (count($following) > 0): ?>
                                <?php foreach ($following as $followed): ?>
                                    <div class="flex items-center p-2 mb-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                                        <img src="<?php echo htmlspecialchars($followed['profile_picture'] ?: generateDefaultAvatar('male')); ?>" alt="Profile Picture" class="profile-pic mr-2">
                                        <a href="?route=profile&user_id=<?php echo $followed['id']; ?>" class="text-sm">@<?php echo htmlspecialchars($followed['username']); ?></a>
                                    </div>
                                <?php endforeach; ?>
                            <?php else: ?>
                                <p class="text-sm">Não está seguindo ninguém.</p>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Postagens do Usuário -->
            <h3 class="text-xl font-bold mb-4">Postagens Recentes</h3>
            <?php if (count($posts) > 0): ?>
                <?php foreach ($posts as $post): ?>
                    <div class="post-card p-4 mb-4">
                        <div class="flex items-center mb-3">
                            <img src="<?php echo htmlspecialchars($post['profile_picture'] ?: generateDefaultAvatar($user['gender'])); ?>" class="profile-pic mr-3" alt="Profile Picture">
                            <a href="?route=profile&user_id=<?php echo $post['user_id']; ?>" class="font-bold">@<?php echo htmlspecialchars($post['username']); ?></a>
                            <span class="text-sm text-gray-500 ml-2"><?php echo date('d/m/Y H:i', strtotime($post['created_at'])); ?></span>
                        </div>
                        <p class="mb-3"><?php echo htmlspecialchars($post['content']); ?></p>
                        <?php if ($post['media_url']): ?>
                            <?php if ($post['media_type'] === 'image'): ?>
                                <img src="<?php echo htmlspecialchars($post['media_url']); ?>" class="post-media" alt="Post Image">
                            <?php elseif ($post['media_type'] === 'video'): ?>
                                <video controls class="post-media">
                                    <source src="<?php echo htmlspecialchars($post['media_url']); ?>" type="video/mp4">
                                    Seu navegador não suporta o elemento de vídeo.
                                </video>
                            <?php endif; ?>
                        <?php endif; ?>
                        <div class="flex items-center text-sm text-gray-500">
                            <span class="mr-3"><?php echo $post['like_count'] ?? 0; ?> curtidas</span>
                            <span><?php echo $post['category'] ? '#' . htmlspecialchars($post['category']) : ''; ?></span>
                        </div>
                        <div class="flex gap-3 mt-3">
                            <button class="action-btn text-gray-500 hover:text-blue-500">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>
                            </button>
                            <button class="action-btn text-gray-500 hover:text-blue-500">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                            </button>
                        </div>
                    </div>
                <?php endforeach; ?>
            <?php else: ?>
                <div class="post-card p-6 text-center">
                    <p>Nenhuma postagem encontrada.</p>
                </div>
            <?php endif; ?>

            <!-- Serviços do Usuário -->
            <h3 class="text-xl font-bold mb-4">Serviços Oferecidos</h3>
            <?php if (count($services) > 0): ?>
                <?php foreach ($services as $service): ?>
                    <div class="post-card p-4 mb-4">
                        <h5 class="font-bold"><?php echo htmlspecialchars($service['name']); ?></h5>
                        <p class="text-sm text-gray-500 mb-2"><?php echo htmlspecialchars($service['description']); ?></p>
                        <div class="flex justify-between items-center">
                            <span class="font-bold">R$<?php echo number_format($service['price'], 2, ',', '.'); ?></span>
                            <a href="?route=chat&user_id=<?php echo $user['id']; ?>" class="btn btn-primary btn-sm">Contatar</a>
                        </div>
                    </div>
                <?php endforeach; ?>
            <?php else: ?>
                <div class="post-card p-6 text-center">
                    <p>Nenhum serviço oferecido.</p>
                </div>
            <?php endif; ?>
        </div>
    <div>

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