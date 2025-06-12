<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'chat');

if (!isset($_SESSION['user_id'])) {
    header("Location: ?route=login");
    exit;
}

$receiver_id = isset($_GET['user_id']) ? (int)$_GET['user_id'] : null;
$current_user_id = $_SESSION['user_id'];

// Processa envio de mensagem
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['message']) && $receiver_id) {
    $message = filter_input(INPUT_POST, 'message', FILTER_SANITIZE_STRING);
    if ($message) {
        $stmt = $pdo->prepare("INSERT INTO messages (sender_id, receiver_id, content, created_at) VALUES (?, ?, ?, NOW())");
        $stmt->execute([$current_user_id, $receiver_id, $message]);
        header("Location: ?route=chat&user_id=$receiver_id");
        exit;
    }
}

// Busca mensagens
$messages = [];
if ($receiver_id) {
    try {
        $stmt = $pdo->prepare("
            SELECT m.*, u.username AS sender_username, u.profile_picture AS sender_picture
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
        ");
        $stmt->execute([$current_user_id, $receiver_id, $receiver_id, $current_user_id]);
        $messages = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        error_log("Erro ao buscar mensagens: " . $e->getMessage());
        $messages = [];
    }
}

// Busca lista de contatos
$stmt = $pdo->prepare("
    SELECT DISTINCT u.id, u.username, u.profile_picture
    FROM messages m
    JOIN users u ON u.id = CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
    WHERE m.sender_id = ? OR m.receiver_id = ?
    ORDER BY m.created_at DESC
");
$stmt->execute([$current_user_id, $current_user_id, $current_user_id]);
$contacts = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Chat</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #0095f6; /* Azul do Instagram */
            --primary-hover: #0077cc;
            --secondary: #f3f4f6;
            --dark-bg: #121212; /* Fundo escuro mais suave */
            --dark-card: #1e1e1e;
            --dark-text: #f5f5f5;
            --dark-border: #333333;
            --light-bg: #fafafa; /* Fundo claro do Instagram */
            --light-card: #ffffff;
            --light-text: #262626;
            --light-border: #dbdbdb; /* Bordas claras do Instagram */
            --message-received: #efefef; /* Bolha de mensagem recebida */
            --message-sent: #0095f6; /* Bolha de mensagem enviada */
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--light-bg);
            color: var(--light-text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .dark {
            background-color: var(--dark-bg);
            color: var(--dark-text);
        }
        
        .dark .chat-card, .dark .message-card, .dark .form-control {
            background-color: var(--dark-card);
            border-color: var(--dark-border);
            color: var(--dark-text);
        }
        
        .dark .text-gray-500 { color: #a0a0a0 !important; }
        .dark .text-gray-300 { color: #d0d0d0 !important; }
        
        .chat-card {
            border: 1px solid var(--light-border);
            background-color: var(--light-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        .message-card {
            border: 1px solid var(--light-border);
            background-color: var(--light-card);
            border-radius: 18px; /* Bordas mais arredondadas como no Instagram */
            padding: 8px 12px;
            margin-bottom: 8px;
            max-width: 70%;
            font-size: 14px;
        }
        
        .message-card.sent {
            background-color: var(--message-sent);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .message-card.received {
            background-color: var(--message-received);
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        
        .dark .message-card.sent {
            background-color: var(--message-sent);
        }
        
        .dark .message-card.received {
            background-color: #333;
        }
        
        .profile-pic {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid var(--light-border);
        }
        
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
        }
        
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        
        .chat-container {
            display: flex;
            height: calc(100vh - 150px);
        }
        
        .contacts-list {
            width: 350px; /* Largura aumentada */
            border-right: 1px solid var(--light-border);
            overflow-y: auto;
            padding: 0;
        }
        
        .dark .contacts-list {
            border-right-color: var(--dark-border);
        }
        
        .contact-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid var(--light-border);
            transition: background-color 0.2s;
        }
        
        .contact-item:hover {
            background-color: rgba(0, 0, 0, 0.03);
        }
        
        .dark .contact-item:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        .contact-info {
            margin-left: 12px;
            flex: 1;
        }
        
        .contact-name {
            font-weight: 600;
        }
        
        .contact-last-message {
            font-size: 13px;
            color: #8e8e8e;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .chat-area {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: 15px;
            border-bottom: 1px solid var(--light-border);
            display: flex;
            align-items: center;
        }
        
        .messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 15px;
            background-color: var(--light-bg);
            background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBvcGFjaXR5PSIwLjA1Ij48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ3aGl0ZSIvPjxwYXRoIGQ9Ik0gMCwwIEwgMjAwLDIwMCBNIDIwMCwwIEwgMCwyMDAiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg==');
            background-size: 40px 40px;
        }
        
        .dark .messages {
            background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBvcGFjaXR5PSIwLjA1Ij48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJibGFjayIvPjxwYXRoIGQ9Ik0gMCwwIEwgMjAwLDIwMCBNIDIwMCwwIEwgMCwyMDAiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg==');
        }
        
        .message-input-container {
            padding: 12px;
            border-top: 1px solid var(--light-border);
            background-color: var(--light-card);
        }
        
        .message-input {
            display: flex;
            align-items: center;
            background-color: var(--light-bg);
            border-radius: 22px;
            padding: 8px 12px;
        }
        
        .dark .message-input {
            background-color: #333;
        }
        
        .message-input input {
            flex: 1;
            border: none;
            background: transparent;
            outline: none;
            padding: 6px 10px;
            font-size: 14px;
            color: var(--light-text);
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .contacts-list {
                width: 100%;
                display: <?php echo $receiver_id ? 'none' : 'block'; ?>;
            }
            
            .chat-area {
                display: <?php echo $receiver_id ? 'flex' : 'none'; ?>;
            }
            
            .back-button {
                display: block;
                margin-right: 12px;
                cursor: pointer;
            }
        }
    </style>
</head>
<body>
    <div class="container mx-auto mt-16 px-4 flex-grow">
        <div class="chat-card">
            <div class="chat-container">
                <!-- Lista de Contatos -->
                <div class="contacts-list">
                    <div class="chat-header">
                        <?php if ($receiver_id): ?>
                            <div class="back-button" onclick="window.history.back()">
                                <i class="fas fa-arrow-left"></i>
                            </div>
                        <?php endif; ?>
                        <h3 class="text-lg font-bold">Conversas</h3>
                    </div>
                    
                    <?php if (count($contacts) > 0): ?>
                        <?php foreach ($contacts as $contact): ?>
                            <a href="?route=chat&user_id=<?php echo $contact['id']; ?>" class="contact-item">
                                <img src="<?php echo htmlspecialchars($contact['profile_picture'] ?: generateDefaultAvatar('male')); ?>" class="profile-pic" alt="Profile Picture">
                                <div class="contact-info">
                                    <div class="contact-name">@<?php echo htmlspecialchars($contact['username']); ?></div>
                                    <div class="contact-last-message">Toque para abrir a conversa</div>
                                </div>
                            </a>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="p-4 text-center text-gray-500">
                            <i class="far fa-comment-dots fa-2x mb-2"></i>
                            <p>Nenhuma conversa iniciada.</p>
                        </div>
                    <?php endif; ?>
                </div>

                <!-- Área de Chat -->
                <div class="chat-area">
                    <?php if ($receiver_id): ?>
                        <?php
                        $stmt = $pdo->prepare("SELECT username, profile_picture FROM users WHERE id = ?");
                        $stmt->execute([$receiver_id]);
                        $recipient = $stmt->fetch();
                        ?>
                        <div class="chat-header">
                            <div class="back-button" onclick="window.history.back()">
                                <i class="fas fa-arrow-left"></i>
                            </div>
                            <img src="<?php echo htmlspecialchars($recipient['profile_picture'] ?: generateDefaultAvatar('male')); ?>" class="profile-pic mr-2" alt="Profile Picture">
                            <h3 class="text-lg font-bold">@<?php echo htmlspecialchars($recipient['username']); ?></h3>
                        </div>
                        <div class="messages" id="messages-container">
                            <?php if (count($messages) > 0): ?>
                                <?php foreach ($messages as $message): ?>
                                    <div class="message-card <?php echo $message['sender_id'] == $current_user_id ? 'sent' : 'received'; ?>">
                                        <div class="d-flex align-items-center mb-1">
                                            <img src="<?php echo htmlspecialchars($message['sender_picture'] ?: generateDefaultAvatar('male')); ?>" class="profile-pic mr-2" alt="Sender Picture">
                                            <span class="font-bold">@<?php echo htmlspecialchars($message['sender_username']); ?></span>
                                        </div>
                                        <p><?php echo htmlspecialchars($message['content']); ?></p>
                                        <small class="message-time"><?php echo date('H:i', strtotime($message['created_at'])); ?></small>
                                    </div>
                                <?php endforeach; ?>
                            <?php else: ?>
                                <div class="text-center mt-8 text-gray-500">
                                    <i class="far fa-comment-dots fa-2x mb-2"></i>
                                    <p>Nenhuma mensagem ainda. Comece a conversa!</p>
                                </div>
                            <?php endif; ?>
                        </div>
                        <div class="message-input-container">
                            <form method="POST" action="?route=chat&user_id=<?php echo $receiver_id; ?>" class="message-input">
                                <input type="text" name="message" placeholder="Digite sua mensagem..." required>
                                <button type="submit" class="btn btn-primary ml-2">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </form>
                        </div>
                    <?php else: ?>
                        <div class="flex items-center justify-center h-full">
                            <div class="text-center text-gray-500">
                                <i class="far fa-comments fa-3x mb-4"></i>
                                <p>Selecione um contato para começar a conversar.</p>
                            </div>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Rolagem automática para baixo
        window.addEventListener('load', function() {
            const container = document.getElementById('messages-container');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        });
        
        // Verificar se estamos em mobile e mostrar apenas a lista ou apenas o chat
        function checkMobileView() {
            if (window.innerWidth <= 768) {
                const urlParams = new URLSearchParams(window.location.search);
                const userId = urlParams.get('user_id');
                
                if (userId) {
                    document.querySelector('.contacts-list').style.display = 'none';
                    document.querySelector('.chat-area').style.display = 'flex';
                } else {
                    document.querySelector('.contacts-list').style.display = 'block';
                    document.querySelector('.chat-area').style.display = 'none';
                }
            }
        }
        
        window.addEventListener('resize', checkMobileView);
        checkMobileView();
    </script>
</body>
</html>