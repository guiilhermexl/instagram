<?php
// Conexão com o banco hospedado no Railway
try {
    $pdo = new PDO(
        "mysql:host=tramway.proxy.rlwy.net;port=12027;dbname=railway;charset=utf8mb4",
        "root",
        "nLrLybfKaZucSbtMIMDtoTiJKjTdCYWq"
    );
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro na conexão com o banco de dados: " . $e->getMessage());
}
?>
