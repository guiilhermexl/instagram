<?php
try {
    $pdo = new PDO("mysql:host=localhost;dbname=evoluir;charset=utf8mb4", "root", "");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro de conexão: " . $e->getMessage());
}

function logVisit($pdo, $page) {
    $user_id = isset($_SESSION['user_id']) ? (int)$_SESSION['user_id'] : null;
    $ip_address = $_SERVER['REMOTE_ADDR'];
    $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';
    
    $stmt = $pdo->prepare("INSERT INTO visits (user_id, page, ip_address, user_agent, visit_time) VALUES (?, ?, ?, ?, NOW())");
    $stmt->execute([$user_id, $page, $ip_address, $user_agent]);
}

function generateDefaultAvatar($gender) {
    if ($gender === 'male') {
        return 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png';
    } elseif ($gender === 'female') {
        return 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png';
    } else {
        return 'https://cdn-icons-png.flaticon.com/512/4140/4140037.png';
    }
}
?>