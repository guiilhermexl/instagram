<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'register');

// Redireciona se já estiver logado
if (isset($_SESSION['user_id'])) {
    header("Location: ?route=feed");
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $full_name = filter_input(INPUT_POST, 'full_name', FILTER_SANITIZE_STRING);
    $username = filter_input(INPUT_POST, 'username', FILTER_SANITIZE_STRING);
    $email = filter_input(INPUT_POST, 'email', FILTER_SANITIZE_EMAIL);
    $password = password_hash($_POST['password'], PASSWORD_BCRYPT);
    $birth_date = filter_input(INPUT_POST, 'birth_date', FILTER_SANITIZE_STRING);
    $gender = filter_input(INPUT_POST, 'gender', FILTER_SANITIZE_STRING);
    $profile_picture = generateDefaultAvatar($gender);

    try {
        $stmt = $pdo->prepare("INSERT INTO users (full_name, username, email, password, birth_date, gender, profile_picture) VALUES (?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([$full_name, $username, $email, $password, $birth_date, $gender, $profile_picture]);
        header("Location: ?route=login");
        exit;
    } catch (PDOException $e) {
        $error = "Erro: Nome de usuário ou email já existe.";
    }
}
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Cadastro</title>
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
        .dark .post-card, .dark .form-control, .dark .form-select {
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
        .dark .post-card {
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
    </style>
</head>
<body>
    <div class="container mx-auto mt-16 px-4 flex-grow">
        <?php if (isset($error)): ?>
            <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <div class="max-w-md mx-auto post-card p-6">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold mb-2">Cadastro</h2>
                <p class="text-sm text-gray-500">Crie sua conta para começar a evoluir</p>
            </div>
            <form method="POST" action="?route=register">
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Nome Completo</label>
                    <input type="text" class="form-control w-full p-2 border rounded" name="full_name" required>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Usuário</label>
                    <input type="text" class="form-control w-full p-2 border rounded" name="username" required>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Email</label>
                    <input type="email" class="form-control w-full p-2 border rounded" name="email" required>
                </div>
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
                    <select class="form-control w-full p-2 border rounded" name="gender" required>
                        <option value="male">Masculino</option>
                        <option value="female">Feminino</option>
                        <option value="other">Outro</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition">Cadastrar</button>
            </form>
        </div>
    </div>
</body>
</html>