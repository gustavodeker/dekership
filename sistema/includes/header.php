<?php // Conexão

require_once 'conexao.php';



// Iniciando sessão

session_start();



// Verificação se está logado

if(!isset($_SESSION['logado'])): //Se não existir sessão logado

    header('Location: loginsistema.php'); //Redirecionar para index.php

endif; //Encerra o if



// Coletando dados do banco com baso na sessão com os dados do usuario

    $id = $_SESSION['id_usuario']; // Array id pega o i_id_usuario que esta como sessão 'id_usuario' coletado na página index de login

    $sql = "SELECT * FROM usuario WHERE i_id_usuario = '$id'"; // Busca os dados no banco com base no id coletado

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

    <title>Sistema</title>

    <link rel="stylesheet" href="../css/stylemenu.css">

    <link rel="stylesheet" href="../css/stylegeral.css">

    <link rel="shortcut icon" href="../imgs/ico.ico" type="image/x-icon">

</head>

<body>

    <input type="checkbox" id="bt-menu">

    <label for="bt-menu">&#9776;</label>

    

<nav class="menu">

    <ul id="menu">

        <li><a href="../home.php">HOME</a></li>

        <li><a href="#">ORÇAMENTOS</a>

            <ul>

                <li><a href="#">CONSULTA</a></li>

                <li><a href="#">ABERTURA</a></li>

            </ul>

        </li>

        <li><a href="#">CLIENTES</a>

            <ul>

                <li><a href="#">CONSULTAR</a></li>

                <li><a href="../adicionar.php">ADICIONAR</a></li>

                <li><a href="#">ATUALIZAR</a></li>

            </ul>

        </li>

        <li><a href="#">VENDAS</a>

            <ul>

                <li><a href="#">CONSULTAR</a></li>

                <li><a href="#">ADICIONAR</a></li>

            </ul>

        </li>

        <li><a href="#">PRODUTOS</a>

            <ul>

                <li><a href="#">CONSULTAR</a></li>

                <li><a href="#">ADICIONAR</a></li>

                <li><a href="#">ATUALIZAR</a></li>

            </ul>

        </li>

        <li><a href="#">MANUAIS</a>

            <ul>

                <li><a href="#">PROCEDIMENTOS</a></li>

                <li><a href="#">VALORES PADRÃO</a></li>

            </ul>

        </li>

        <li><a href="../flexbox/musics.html">MUSICS</a>

        </li>

        </li>

        <li><a href="../game/loginsistema.php">GAME</a>

        </li>

    </ul>

</nav>

<h5>Wellcome, <?php echo $dados['v_nome_usuario']; //seleciona o índice v_nome_usuario do array $dados que foi coletado?> ! <a href="logout.php"><button id="btn-logout">Sair</button></a></h5>

