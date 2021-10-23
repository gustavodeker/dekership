<?php

    require_once 'includes/conexao.php'; // Conexão



    session_start(); // Sessão



    // Tratamentos ao clicar no botão de entrar

    if(isset($_POST['btn_entrar_login'])): //Se existir o POST, ou seja, se o botão entrar for pressionado

        $erros = array(); // Cria um array para possíveis erros

        // Ao clicar no btn ele captura o texto dos campos usuário e senha em variáveis

        $login = mysqli_escape_string($con, $_POST['usuario_login']);

        $senha = mysqli_escape_string($con, $_POST['usuario_senha']);



        // Tratamento de erro

        if(empty($login) or empty($senha)): // Se um dos campos estiver vazio

            $erros[] = "<li> Os campos Usuário e Senha são obrigatórios.</li>"; // Inclui esse texto como um índice no array de erros

        // Se nenhum dos dois estiver vazio, então prossegue fazendo a verificação de login

        else:

            // SQL de consulta onde relaciona login AND senha com as colunas e as variáveis $login AND $senha criadas para capturar os textos dos campos digitados

            $sql = "SELECT * FROM usuario WHERE v_usuario_usuario = '$login' AND v_senha_usuario = '$senha'";

            // Resultado gerado a partir da query, Conexão + comando sql, armazenado na variável $resultado

            $resultado = mysqli_query($con, $sql);

                // Verificando se a consulta no banco de dados gerou uma linha, ou seja, se foram encontrados os campos login e senha corretos e geraram 1 resultado no insert

                if(mysqli_num_rows($resultado) > 0): // Se o número de linhas do resultado do insert for maior que 0 (se encontrou alguma coisa)

                    $dados = mysqli_fetch_array($resultado); // Converte os dados do resultado em um array para variável $dados

                    mysqli_close($con); // Fecha conexão após acabar de usar o banco de dados

                    $_SESSION['logado'] = true; // Criar sessão logado

                    $_SESSION['id_usuario'] = $dados['i_id_usuario']; // Criar sessão para tornar os dados de usuário globais

                    header('Location: /pgs/home.php'); // Redirecionar para a página home.php

                else:

                    $erros[] = "<li> Usuário ou senha incorretos.</li>"; // Inclui esse texto como um índice no array de erros

                endif;

         endif;

    endif;

?>



<!DOCTYPE html>

<html lang="pt-br">

<head>

    <meta charset="UTF-8">

    <meta http-equiv="X-UA-Compatible" content="IE=edge">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Sistema</title>

    <link rel="shortcut icon" href="favicon.ico">

    <style>

        .container {

        width: 100vw;

        height: 100vh;

        background-image: url(imgs/wallpaperlogin.jpg);

        background-size: cover;

        display: flex;

        flex-direction: row;

        justify-content: center;

        align-items: center;

        }

        .box {

        width: 200px;

        height: 150px;

        background: #fff;

        display: flex;

        flex-direction: row;

        justify-content: center;

        align-items: center;

        margin-bottom: 300px;

        border-radius: 10px;

        opacity: 0.9;

        padding: 0px 20px 0px 20px;

        }

        body {

        margin: 0px;

        }

    </style>

</head>

<body>

    <?php

    // Mostrar erros de login logo acima do formulário

    if(!empty($erros)): //Se não estiver vazio, é porque contem erro, então:

        foreach($erros as $erro): // (foreach porque é um array, então "para cada erro", exibe os erros

            echo $erro; // Exibe o erro se houver

        endforeach; // Encerra o foreach

    endif; // Encerra o if

    ?>

    <div class="container">

        <div class="box">

        <form action="" method="POST">

            <label>Usuário:</label><br><input name="usuario_login" type="text" required minlength="1" maxlength="20"> <br>

            <label>Senha:</label><br><input name="usuario_senha" type="password" required minlength="1" maxlength="20" ><br>

            <button type="submit" name="btn_entrar_login">Entrar</button>

        </form>

        </div>

    </div>    

</body>

</html>