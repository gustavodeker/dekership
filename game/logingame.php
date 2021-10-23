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
            background-image: url("imgs/fundologin.jpg");
            background-repeat: none;
            background-size: auto;
            background-attachment: fixed;
        }
        .telaLoginGame{
            background-color: rgba(0, 0, 0, 0.2);
            position: absolute; /* deixar o tamanho contido */
            top: 5%; /* posicionar ao centro */
            left: 0%; /* posicionar ao centro */
            transform: translate(0%, 0%); /* O ponto central considerado da div no caso seria o vertice superior direito, para centralizar o ponto de foco na div é feito dessa forma */
            padding: 1%;
            border-radius: 10px;
            color: white;
            text-align: center;
            display: grid;
            gap: 1px;
            grid-template-columns: auto auto 10%;
            grid-auto-rows: auto;
            grid-template-areas: ". form col4";
            width: 98%;
        }
        form{
            grid-area: form;
            display: grid;
            grid-template-columns: auto auto auto;
            gap: 2%;
            align-items: center; 
            grid-template-areas: "col1 col2 col3";
        }
        input{
            padding: 2%;
            border: none; /* tira borda */
            outline: none; /* tira a outline quando o input está selecionado */
            font-size: 15px;
            color: #55f;
        }
        .inputSubmit{
            background-color: #55f;
            border: none;
            padding: 10px;
            width: 100%;
            border-radius: 5px;
            color: white;
            font-size: 15px;
            cursor: pointer; /* cursor de mãozinha ao colocar o mouse encima*/
        }
        .col1{
            grid-area: col1;
        }
        .col2{
            grid-area: col2;
        }
        .col3{
            grid-area: col3;
        }
        .col4{
            grid-area: col4;    
        }
        div{
            align-items: center;
        }
        input{
            width: 100%;
        }
        
        .inputSubmit:hover{
            background-color: rgb(68, 68, 202);
        }
        .inputSubmit2{
            background-color: #55f;
            border: none;
            padding: 10px;
            width: 100%;
            border-radius: 5px;
            color: white;
            font-size: 15px;
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
        <?php // Erro ao deixar os campos nickname ou senha vazios
        if(!empty($erros)):
            foreach($erros as $erro):
                echo $erro;
            endforeach;
        endif;
        ?>
        <form action="<?php echo $_SERVER['PHP_SELF'];?>" method="POST">  <!-- Retorna a própria página como action -->
            <div class="col1">
                <input type="text" class="nickname" name="nickname" placeholder="Nickname" required>
            </div>
            <div class="col2">
                <input type="password" class="senha" name="senha" placeholder="Senha" required>
            </div>
            <div class="col3">
                <button class="inputSubmit" type="submit" name="btn_entrar"> Entrar </button>
            </div>
        </form>
            <div class="col4">
                <a href="cadastrogame.php"><button class="inputSubmit2">Cadastrar-se</button></a>
            </div>
    </div>
    
</body>
</html>