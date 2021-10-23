<?php
// Conexão
require 'conexao.php';
// Iniciando sessão
session_start();

// Verificação se está logado
if(!isset($_SESSION['logado'])): //Se não existir sessão logado
    header('Location: logingame.php'); //Redirecionar para index.php
endif; //Encerra o if

// Coletando dados do banco com baso na sessão com os dados do usuario
    $id = $_SESSION['id']; // Array id pega o i_id_usuario que esta como sessão 'id_usuario' coletado na página index de login
    $sql = "SELECT * FROM gplayers WHERE id = '$id'"; // Busca os dados no banco com base no id coletado
    $resultado = mysqli_query($con, $sql); // Salva na variável o resultado da conexão + consulta
    $dados = mysqli_fetch_array($resultado); // Transforma os dados coletados em array para a variável $dados
    mysqli_close($con); // fecha a conexão do banco após acabar de usar
?>


<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="css/estiloheader.css">
</head>
<body>
    <input type="checkbox" id="bt-menu">
    <label for="bt-menu">&#9776;</label>
<nav class="menu">
    <ul id="menu">
        <li><a href="game.php">Início</a></li>

        <!--<li><a href="#">Perfil</a>
            <ul>
                <li><a href="#">Histórico</a></li>
                <li><a href="#">Dados</a></li>
            </ul>
        </li>
        -->
        <li><a href="#">Ranking</a>
            <ul>
                <!--<li><a href="#">Mensal</a></li>-->
                <li><a href="rankingglobal.php">Global</a></li>
            </ul>
        <li><a href="logout.php" id="nickname" style="background-color: rgb(125, 125, 250); font-size: 12px; margin-top: 3px; border-radius: 5px; ">
        <?php echo $dados['nickname'];?> | Sair</a>
    </ul>
</nav>

