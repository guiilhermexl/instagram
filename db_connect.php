<?php
$host = 'tramway.proxy.rlwy.net';
$port = 12027;
$dbname = 'railway';
$username = 'root';
$password = 'nLrLybfKaZucSbtMIMDtoTiJKjTdCYWq';

try {
    $pdo = new PDO("mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro de conexão: " . $e->getMessage());
}
