<?php

declare(strict_types=1);

if (current_user() !== null) {
    redirect_to('lobby');
}

$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string) ($_POST['username'] ?? ''));
    $email = trim((string) ($_POST['email'] ?? ''));
    $password = trim((string) ($_POST['password'] ?? ''));
    $confirmPassword = trim((string) ($_POST['confirm_password'] ?? ''));

    if ($username === '' || $email === '' || $password === '') {
        $error = 'Preencha todos os campos';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Email invalido';
    } elseif ($password !== $confirmPassword) {
        $error = 'Senhas diferentes';
    } else {
        try {
            if (register_user($username, $email, $password)) {
                if (login_user($username, $password)) {
                    redirect_to('lobby');
                }
                redirect_to('login');
            }
        } catch (PDOException) {
            $error = 'Usuario ou email ja cadastrado';
        }
    }
}

render_header('Cadastro');
?>
<section class="panel narrow">
    <h1>Cadastro</h1>
    <?php if ($error !== null): ?>
        <div class="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
    <?php endif; ?>
    <form method="post" class="stack">
        <label>
            <span>Usuario</span>
            <input type="text" name="username" maxlength="50" required>
        </label>
        <label>
            <span>Email</span>
            <input type="email" name="email" maxlength="255" required>
        </label>
        <label>
            <span>Senha</span>
            <input type="password" name="password" minlength="6" required>
        </label>
        <label>
            <span>Confirmar senha</span>
            <input type="password" name="confirm_password" minlength="6" required>
        </label>
        <button type="submit">Cadastrar</button>
    </form>
    <div class="muted">
        <a href="/index.php?page=login">Voltar para login</a>
    </div>
</section>
<?php render_footer(); ?>
