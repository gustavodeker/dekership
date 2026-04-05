<?php

declare(strict_types=1);

if (current_user() !== null) {
    redirect_to('lobby');
}

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string) ($_POST['username'] ?? ''));
    $password = trim((string) ($_POST['password'] ?? ''));
    if (login_user($username, $password)) {
        redirect_to('lobby');
    }
    $error = 'Credenciais invalidas';
}

render_header('Login');
?>
<section class="panel narrow">
    <h1>Login</h1>
    <?php if ($error !== null): ?>
        <div class="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
    <?php endif; ?>
    <form method="post" class="stack">
        <label>
            <span>Usuario</span>
            <input type="text" name="username" required>
        </label>
        <label>
            <span>Senha</span>
            <input type="password" name="password" required>
        </label>
        <button type="submit">Entrar</button>
    </form>
    <div class="muted">
        <a href="/index.php?page=cadastro">Criar conta</a>
    </div>
</section>
<?php render_footer(); ?>
