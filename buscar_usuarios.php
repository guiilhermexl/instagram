<?php
require_once 'db_connect.php';
header('Content-Type: application/json');

if (!isset($_GET['q']) || trim($_GET['q']) === '') {
    echo json_encode([]);
    exit;
}

$q = '%' . trim($_GET['q']) . '%';

try {
    $stmt = $pdo->prepare("SELECT id, username, full_name, profile_picture FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT 10");
    $stmt->execute([$q, $q]);
    $usuarios = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($usuarios);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Erro ao buscar usuários: ' . $e->getMessage()]);
}
?>
