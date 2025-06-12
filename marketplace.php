<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'db_connect.php';
logVisit($pdo, 'marketplace');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_STRING);
    $description = filter_input(INPUT_POST, 'description', FILTER_SANITIZE_STRING);
    $price = filter_input(INPUT_POST, 'price', FILTER_VALIDATE_FLOAT);
    $category = filter_input(INPUT_POST, 'category', FILTER_SANITIZE_STRING);

    if ($name && $description && $price !== false && $category) {
        $stmt = $pdo->prepare("INSERT INTO services (user_id, name, description, price, category, created_date, is_active) VALUES (?, ?, ?, ?, ?, NOW(), 1)");
        $stmt->execute([$_SESSION['user_id'], $name, $description, $price, $category]);
        header("Location: ?route=marketplace");
        exit;
    } else {
        $error = "Por favor, preencha todos os campos corretamente.";
    }
}

$category_filter = isset($_GET['category']) ? filter_input(INPUT_GET, 'category', FILTER_SANITIZE_STRING) : '';
$query = "SELECT s.*, u.username FROM services s JOIN users u ON s.user_id = u.id WHERE s.is_active = 1";
if ($category_filter) {
    $query .= " AND s.category = ?";
    $stmt = $pdo->prepare($query);
    $stmt->execute([$category_filter]);
} else {
    $stmt = $pdo->query($query);
}
$services = $stmt->fetchAll();
?>

<!DOCTYPE html>
<html lang="pt-BR" class="<?php echo isset($_SESSION['theme']) && $_SESSION['theme'] === 'dark' ? 'dark' : 'light'; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evoluir - Marketplace</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1877f2;
            --primary-hover: #166fe5;
            --secondary: #f0f2f5;
            --dark-bg: #18191a;
            --dark-card: #242526;
            --dark-text: #e4e6eb;
            --dark-border: #3e4042;
            --light-bg: #f0f2f5;
            --light-card: #ffffff;
            --light-text: #050505;
            --light-border: #dddfe2;
            --green-price: #42b72a;
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
        .dark .text-gray-500 { color: #b0b3b8 !important; }
        .dark .text-gray-300 { color: #e4e6eb !important; }
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
        .marketplace-header {
            background-color: var(--light-card);
            padding: 15px 0;
            border-bottom: 1px solid var(--light-border);
        }
        .dark .marketplace-header {
            background-color: var(--dark-card);
            border-bottom: 1px solid var(--dark-border);
        }
        .post-card {
            border: 1px solid var(--light-border);
            background-color: var(--light-card);
            margin-bottom: 16px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .post-card:hover {
            transform: translateY(-2px);
        }
        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
            font-weight: 600;
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .btn-success {
            background-color: var(--green-price);
            border-color: var(--green-price);
        }
        .btn-success:hover {
            background-color: #36a420;
            border-color: #36a420;
        }
        .price-tag {
            color: var(--green-price);
            font-weight: bold;
        }
        .category-chip {
            display: inline-block;
            padding: 4px 12px;
            background-color: #e7f3ff;
            border-radius: 16px;
            color: var(--primary);
            font-size: 14px;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .dark .category-chip {
            background-color: #3a3b3c;
            color: #2d88ff;
        }
        .add-product-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 100;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .search-box {
            background-color: white;
            border-radius: 50px;
            padding: 8px 12px;
            width: 100%;
            max-width: 500px;
        }
        .dark .search-box {
            background-color: #3a3b3c;
            color: white;
        }
    </style>
</head>
<body>
    <div class="marketplace-header">
        <div class="container mx-auto">
            <h1 class="text-2xl font-bold">Marketplace</h1>
        </div>
    </div>

    <div class="container mx-auto mt-4 px-4 flex-grow">
        <div class="flex flex-col md:flex-row gap-6">
            <!-- Filtros/Categorias -->
            <div class="w-full md:w-1/4">
                <div class="post-card p-4 mb-4 sticky top-20">
                    <h3 class="font-bold mb-3">Categorias</h3>
                    <div class="flex flex-wrap">
                        <a href="?route=marketplace" class="category-chip <?php echo !$category_filter ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">Todos</a>
                        <a href="?route=marketplace&category=consultoria" class="category-chip <?php echo $category_filter === 'consultoria' ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">#consultoria</a>
                        <a href="?route=marketplace&category=design" class="category-chip <?php echo $category_filter === 'design' ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">#design</a>
                        <a href="?route=marketplace&category=tecnologia" class="category-chip <?php echo $category_filter === 'tecnologia' ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">#tecnologia</a>
                        <a href="?route=marketplace&category=educacao" class="category-chip <?php echo $category_filter === 'educacao' ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">#educacao</a>
                        <a href="?route=marketplace&category=saude" class="category-chip <?php echo $category_filter === 'saude' ? 'bg-blue-100 dark:bg-blue-900' : ''; ?>">#saude</a>
                    </div>
                </div>
            </div>

            <!-- Lista de Produtos -->
            <div class="w-full md:w-3/4">
                <!-- Barra de Pesquisa -->
                <div class="mb-6">
                    <form method="GET" action="?route=marketplace" class="flex gap-2">
                        <input type="hidden" name="route" value="marketplace">
                            <input type="search-box form-control" type="text" name="search" placeholder="Pesquisar no Marketplace..." value="<?php echo isset($_GET['search']) ? htmlspecialchars($_GET['search']) : ''; ?>">
                            <button type="submit" class="btn btn-primary">Buscar</button>
                    </form>
                </div>

                <!-- Lista de Serviços -->
                <?php if (count($services) > 0): ?>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <?php foreach ($services as $service): ?>
                            <div class="post-card">
                                <div class="p-4">
                                    <div class="flex items-center mb-3">
                                        <a href="?route=profile&user_id=$post['user_id'] ?>" class="font-semibold text-sm">@<?php echo htmlspecialchars($service['username']); ?></a>
                                    </div>
                                    <h5 class="font-bold mb-2"><?php echo htmlspecialchars($service['name']); ?></h5>
                                        <p class="text-sm text-gray-500 mb-3"><?php echo htmlspecialchars($service['description']); ?></p>
                                        <div class="flex justify-between items-center">
                                            <span class="price-tag">R$<?php echo number_format($service['price'], 2, ',', '.'); ?></span>
                                            <a href="?route=chat&user_id=<?php echo $service['user_id']; ?>" class="btn btn-success btn-sm">Contatar</a>
                                        </div>
                                        <?php if ($service['category']): ?>
                                            <div class="mt-3">
                                                <span class="text-xs text-gray-500"><?php echo htmlspecialchars($service['category']); ?></span>
                                            </div>
                                        <?php endif; ?>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php else: ?>
                        <div class="post-card p-6 text-center">
                            <p>Nenhum serviço encontrado.</p>
                            <a href="#" class="btn btn-primary mt-3" data-bs-toggle="modal" data-bs-target="#addProductModal">Anunciar agora</a>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>

    <!-- Modal para Adicionar Produto -->
    <div class="modal fade" id="addProductModal" tabindex="-1" aria-labelledby="addProductModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="addProductModalLabel">Anunciar Produto/Serviço</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <?php if (isset($error)): ?>
                        <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
                    <?php endif; ?>
                    <form method="POST" action="?route=marketplace">
                        <div class="mb-3">
                            <label class="block text-sm font-medium mb-1">Nome do Produto/Serviço</label>
                            <input type="text" class="form-control w-full p-2 border rounded" name="name" required>
                        </div>
                        <div class="mb-3">
                            <label class="block text-sm font-medium mb-1">Descrição</label>
                            <textarea class="form-control w-full p-2 border rounded" name="description" rows="4" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="block text-sm font-medium mb-1">Preço (R$)</label>
                            <input type="number" class="form-control w-full p-2 border rounded" name="price" step="0.01" required>
                        </div>
                        <div class="mb-3">
                            <label class="block text-sm font-medium mb-1">Categoria</label>
                            <select class="form-select w-full p-2 border rounded" name="category" required>
                                <option value="">Selecione uma categoria</option>
                                <option value="#consultoria">Consultoria</option>
                                <option value="#design">Design</option>
                                <option value="#tecnologia">Tecnologia</option>
                                <option value="#educacao">Educação</option>
                                <option value="#saude">Saúde</option>
                            </select>
                        </div>
                        <div class="flex justify-end gap-2">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="submit" class="btn btn-primary">Enviar</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Botão Flutuante para Adicionar Produto -->
    <button class="add-product-btn btn btn-primary" data-bs-toggle="modal" data-bs-target="#addProductModal">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
        </svg>
    </button>

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