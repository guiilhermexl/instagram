<?php
$host = getenv("DB_HOST");
$port = getenv("DB_PORT") ?: 3306;
$dbname = getenv("DB_NAME");
$username = getenv("DB_USER");
$password = getenv("DB_PASS");

try {
    $pdo = new PDO("mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro de conexão: " . $e->getMessage());
}
