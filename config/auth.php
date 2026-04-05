<?php
if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}
date_default_timezone_set('America/Sao_Paulo');

function loadEnvFile(string $path): void
{
    if (!is_file($path) || !is_readable($path)) {
        return;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return;
    }

    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#') || !str_contains($line, '=')) {
            continue;
        }

        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);
        $value = trim($value, "\"'");

        if ($key !== '' && getenv($key) === false) {
            putenv("{$key}={$value}");
            $_ENV[$key] = $value;
        }
    }
}

loadEnvFile(__DIR__ . '/../.env');

$servidor = getenv('DB_HOST') ?: '127.0.0.1';
$porta = (int)(getenv('DB_PORT') ?: '3306');
$usuario = getenv('DB_USER') ?: 'root';
$senha = getenv('DB_PASS') ?: '';
$banco = getenv('DB_NAME') ?: 'dekership';

try {
    $pdo = new PDO("mysql:host={$servidor};port={$porta};dbname={$banco};charset=utf8mb4", $usuario, $senha);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (PDOException $erro) {
    http_response_code(500);
    exit('Falha ao conectar no banco.');
}

function wsUrl(): string
{
    return getenv('WS_URL') ?: 'ws://127.0.0.1:8765/ws';
}

function cadastro(): void
{
    global $pdo;
    $usuario = limpaPost(strtolower($_POST['usuario'] ?? ''));
    $email = limpaPost($_POST['email'] ?? '');
    $senha = limpaPost($_POST['senha'] ?? '');
    $senha_cript = password_hash($senha, PASSWORD_ARGON2ID);

    if (!preg_match('/^[A-Za-z0-9-]+$/', $usuario)) {
        $_SESSION['mensagemerro'] = 'Apenas letras e numeros no usuario!';
    }

    if (strlen($senha) < 6) {
        $_SESSION['mensagemerro'] = 'Senha deve ter 6 caracteres ou mais!';
    }

    if (!isset($_SESSION['mensagemerro'])) {
        $sql = $pdo->prepare('SELECT id FROM usuario WHERE usuario = ? OR email = ? LIMIT 1');
        $sql->execute([$usuario, $email]);
        $user = $sql->fetch();

        if (!$user) {
            $data = date('Y-m-d H:i:s');
            $sql = $pdo->prepare('INSERT INTO usuario VALUES (NULL, ?, ?, ?, NULL, ?)');
            $sql->execute([$usuario, $email, $senha_cript, $data]);
            $_SESSION['mensagem'] = 'Cadastrado com sucesso!';
        } else {
            $_SESSION['mensagemerro'] = 'Usuario ou email ja cadastrados!';
        }
    }
}

function verificaLogin(): void
{
    global $pdo;
    $name = limpaPost(strtolower($_POST['usuario'] ?? ''));
    $senha = limpaPost($_POST['senha'] ?? '');

    $sql = $pdo->prepare('SELECT * FROM usuario WHERE usuario = ? LIMIT 1');
    $sql->execute([$name]);
    $usuario = $sql->fetch();

    if ($usuario && password_verify($senha, $usuario['senha'])) {
        $token = sha1(uniqid('', true) . date('YmdHis'));
        $sql = $pdo->prepare('UPDATE usuario SET token = ? WHERE usuario = ?');
        $sql->execute([$token, $name]);

        $_SESSION['TOKEN'] = $token;
        $_SESSION['mensagem'] = 'Login com sucesso!';
        header('Location: index.php?page=lobby');
        exit;
    }

    $_SESSION['mensagemerro'] = 'Dados incorretos, tente novamente!';
}

function limpaPost(string $dados): string
{
    $dados = trim($dados);
    $dados = stripslashes($dados);
    $dados = htmlspecialchars($dados, ENT_QUOTES, 'UTF-8');
    return $dados;
}

function auth(string $tokenSessao): array|false
{
    global $pdo;
    $sql = $pdo->prepare('SELECT * FROM usuario WHERE token = ? LIMIT 1');
    $sql->execute([$tokenSessao]);
    $usuario = $sql->fetch();
    return $usuario ?: false;
}

function sessionVerif(): void
{
    global $usuario;
    if (!isset($_SESSION['TOKEN'])) {
        header('Location: index.php?page=login');
        exit;
    }

    $usuario = auth($_SESSION['TOKEN']);
    if (!$usuario) {
        session_unset();
        session_destroy();
        header('Location: index.php?page=login');
        exit;
    }
}

function userStats(int $userId): array
{
    global $pdo;
    $sql = $pdo->prepare('SELECT wins, losses, disconnects FROM player_stats WHERE user_id = ? LIMIT 1');
    $sql->execute([$userId]);
    $stats = $sql->fetch();

    return $stats ?: ['wins' => 0, 'losses' => 0, 'disconnects' => 0];
}

function notyfOK(): void
{
    if (isset($_SESSION['mensagem'])) {
        $mensagem = $_SESSION['mensagem'];
        ?>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">
        <script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>
        <script>
            new Notyf().success(<?= json_encode($mensagem) ?>);
        </script>
        <?php
        unset($_SESSION['mensagem']);
    }
}
register_shutdown_function('notyfOK');

function notyfERRO(): void
{
    if (isset($_SESSION['mensagemerro'])) {
        $mensagemerro = $_SESSION['mensagemerro'];
        ?>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">
        <script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>
        <script>
            new Notyf().error(<?= json_encode($mensagemerro) ?>);
        </script>
        <?php
        unset($_SESSION['mensagemerro']);
    }
}
register_shutdown_function('notyfERRO');