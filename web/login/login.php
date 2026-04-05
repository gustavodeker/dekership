<?php
include 'config/auth.php';
if (isset($_POST['usuario']) && isset($_POST['senha']) && !empty($_POST['usuario']) && !empty($_POST['senha'])) {
    verificaLogin();
}

?>

<!DOCTYPE html>
<html lang="pt-br">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dekership</title>
    <link rel="stylesheet" href="web/login/login.css">
</head>

<body>
    <div class="telaLoginGame">
 
        <h1>Dekership</h1>
        <form method="POST"> <!-- Retorna a própria página como action -->
            <input type="text" class="usuario" name="usuario" placeholder="Usuário" required>
            <input type="password" class="senha" name="senha" placeholder="Senha" required>
            <input class="inputSubmit" type="submit" name="submit" value="Entrar"></input>
        </form>
        <a href="index.php?page=cadastro">Cadastrar-se</a>
    </div>

</body>

</html>