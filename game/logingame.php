<?php
    require 'includes/action_login.php';
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game - Login</title>
    <style>
        body{
            font-family: Arial, Helvetica, sans-serif;
            background-color: rgb(252, 240, 231);
        }
        .telaLoginGame{
            background-color: rgba(0, 0, 0, 0.2);
            position: absolute; /* deixar o tamanho contido */
            top: 50%; /* posicionar ao centro */
            left: 50%; /* posicionar ao centro */
            transform: translate(-50%,-50%); /* O ponto central considerado da div no caso seria o vertice superior direito, para centralizar o ponto de foco na div é feito dessa forma */
            padding: 50px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        input{
            padding: 10px;
            border: none; /* tira borda */
            outline: none; /* tira a outline quando o input está selecionado */
            font-size: 15px;
            color: #55f;
        }
        .inputSubmit{
            background-color: #55f;
            border: none;
            padding: 15px;
            width: 100%;
            border-radius: 5px;
            color: white;
            font-size: 15px;
            cursor: pointer; /* cursor de mãozinha ao colocar o mouse encima*/
        }
        .inputSubmit:hover{
            background-color: rgb(68, 68, 202);
        }
        .inputSubmit2{
            margin-top: 5px;
            background-color: #55f;
            border: none;
            padding: 12px;
            width: 90%;
            border-radius: 5px;
            color: white;
            font-size: 13px;
            cursor: pointer; /* cursor de mãozinha ao colocar o mouse encima*/
        }
        .inputSubmit2:hover{
            background-color: rgb(68, 68, 202);
        }
        li{
            list-style: none;
            margin-bottom: 5px;
        }

    </style>
</head>
<body>
    
    <div class="telaLoginGame">
        <h1>Login</h1>
        <?php // Erro ao deixar os campos nickname ou senha vazios
        if(!empty($erros)):
            foreach($erros as $erro):
                echo $erro;
            endforeach;
        endif;
        ?>
        <form action="<?php echo $_SERVER['PHP_SELF'];?>" method="POST">  <!-- Retorna a própria página como action -->
            <input type="text" name="nickname" placeholder="Nickname" required>
            <br><br>
            <input type="password" name="senha" placeholder="Senha" required>
            <br><br>
            <button class="inputSubmit" type="submit" name="btn_entrar"> Entrar </button>
        </form>
            <hr>
            <a href="cadastrogame.php"><button class="inputSubmit2">Cadastrar-se</button></a>
    </div>
    
</body>
</html>