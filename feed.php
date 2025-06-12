<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'feed');

// Processa nova postagem
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $content = filter_input(INPUT_POST, 'content', FILTER_SANITIZE_STRING);
    $category = filter_input(INPUT_POST, 'category', FILTER_SANITIZE_STRING);
    $media_type = 'text';
    $media_url = null;

    if (isset($_FILES['media']) && $_FILES['media']['error'] === UPLOAD_ERR_OK) {
        $upload_dir = 'Uploads/';
        if (!is_dir($upload_dir)) {
            mkdir($upload_dir, 0755, true);
        }
        $file_ext = pathinfo($_FILES['media']['name'], PATHINFO_EXTENSION);
        $file_name = uniqid() . '.' . $file_ext;
        $file_path = $upload_dir . $file_name;
        if (move_uploaded_file($_FILES['media']['tmp_name'], $file_path)) {
            $media_url = $file_path;
            $media_type = strpos($_FILES['media']['type'], 'image') !== false ? 'image' : 'video';
        }
    }

    $stmt = $pdo->prepare("INSERT INTO posts (user_id, content, category, media_type, media_url, created_at) VALUES (?, ?, ?, ?, ?, NOW())");
    $stmt->execute([$_SESSION['user_id'], $content, $category, $media_type, $media_url]);
    header("Location: ?route=feed");
    exit;
}

// Busca postagens
$category_filter = isset($_GET['category']) ? filter_input(INPUT_GET, 'category', FILTER_SANITIZE_STRING) : '';
$query = "SELECT p.*, u.username, u.profile_picture FROM posts p JOIN users u ON p.user_id = u.id";
if ($category_filter) {
    $query .= " WHERE p.category = ?";
    $stmt = $pdo->prepare($query);
    $stmt->execute([$category_filter]);
} else {
    $stmt = $pdo->query($query);
}
$posts = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Feed</title>
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
        <div class="max-w-2xl mx-auto">
            <!-- Formulário de Nova Postagem -->
            <div class="post-card p-4 mb-6">
                <form method="POST" action="?route=feed" enctype="multipart/form-data">
                    <div class="flex items-center mb-3">
                        <img src="<?php echo htmlspecialchars($_SESSION['profile_picture'] ?? generateDefaultAvatar('male')); ?>" class="profile-pic mr-3" alt="Profile Picture">
                        <span class="font-bold">@<?php echo htmlspecialchars($_SESSION['username']); ?></span>
                    </div>
                    <div class="mb-3">
                        <textarea class="form-control w-full p-3 border rounded" name="content" rows="4" placeholder="No que você está pensando?" required></textarea>
                    </div>
                    <div class="mb-3">
                        <input type="text" class="form-control w-full p-2 border rounded" name="category" placeholder="Hashtag (ex: #educacaofinanceira)" pattern="#\w+">
                    </div>
                    <div class="mb-3">
                        <label class="block text-sm font-medium mb-1">Adicionar Mídia</label>
                        <input type="file" class="form-control w-full p-2 border rounded" name="media" accept="image/*,video/*">
                    </div>
                    <div class="flex justify-end">
                        <button type="submit" class="btn btn-primary px-4 py-2">Postar</button>
                    </div>
                </form>
            </div>

            <!-- Exibição de Postagens -->
            <h3 class="text-xl font-bold mb-4">Feed de Publicações</h3>
            <?php if (count($posts) > 0): ?>
                <?php foreach (array_slice($posts, 0, max(2, count($posts))) as $post): ?>
                    <div class="post-card p-4 mb-4">
                        <div class="flex items-center mb-3">
                            <img src="<?php echo htmlspecialchars($post['profile_picture'] ?: generateDefaultAvatar('male')); ?>" class="profile-pic mr-3" alt="Profile Picture">
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
                    <p>Nenhuma publicação encontrada. Comece postando algo!</p>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>