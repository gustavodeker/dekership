<?php
include('config/auth.php');
if (isset($_POST['submit'])) {
    cadastro();
}
?>

<!DOCTYPE html>
<html lang="pt-br">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game - Cadastro</title>
    <link rel="stylesheet" href="web/cadastro/cadastro.css">
</head>

<body>
    <div class="telaLoginGame">
        <form class="form-cadastro" method="POST">
            <div class="div-input">
                <label for="usuario" class="labelInput">Usuário:</label>
                <input type="text" name="usuario" id="usuario" class="inputUser" required>
            </div>

            <div class="div-input">
                <label for="email" class="labelInput">Email:</label>
                <input type="text" name="email" id="email" class="inputUser" required>
            </div>

            <div class="div-input">
                <label for="senha" class="labelInput">Senha:</label>
                <input type="password" name="senha" id="senha" class="inputUser" required>
            </div>
            <input type="submit" name="submit" id="cadastrar" class="inputSubmit" value="Cadastrar">
        </form>

        <button class="login" onclick="window.location.href='index.php?page=login'">Login</button>
    </div>

</body>

</html>