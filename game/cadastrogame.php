<?php
    if(isset($_POST['submit'])){
        include('includes/conexao.php');
        $nome = $_POST['nome'];
        $nasc = $_POST['nasc'];
        $sexo = $_POST['sexo'];
        $email = $_POST['email'];
        $nickname = $_POST['nickname'];
        $senha = $_POST['senha'];

        $result = mysqli_query($con, "INSERT INTO gplayers (nome,nasc,sexo,email,nickname,senha) VALUES ('$nome','$nasc','$sexo','$email','$nickname','$senha')");
    }
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game - Cadastro</title>
    <style>
        body{
            font-family: Arial, Helvetica, sans-serif;
            background-color: rgb(252, 240, 231);
        }
        .box{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(255,255,255,0.5);
            color: rgb(20, 20, 20);
            padding: 15px;
            border-radius: 10px;
        }
        fieldset{
            border: 3px solid #55f;
        }
        legend{
            border: 1px solid #55f;
            padding: 10px;
            color: white;
            text-align: center;
            background-color: #55f;
            border-radius: 10px;
        }
        .inputBox{
            position: relative;
        }
        .inputUser{
            background: none;
            border: none;
            border-bottom: 1px solid rgb(20, 20, 20);
            outline: none;
            color: rgb(20, 20, 20);
            font-size: 15px;
            width: 100%;
            letter-spacing: 2px; /* espaçamento entre caracteres*/
        }
        .labelInput{
            position: absolute; /* deixa o label dentro do input*/
            top: 0px;
            left: 0px;
            pointer-events: none;/* qualquer lugar que clicar no input vai executar a ação*/
            transition: 0.5s;
        }
        .inputUser:focus ~ .labelInput,
        .inputUser:valid ~ .labelInput { /* quando clicar no input EXECUTA uma ação no labelInput*/
            top: -18px;
            font-size: 13px;
            color: #55f;
        }

        #nasc{
            border: none;
            padding: 5px;
            border-radius: 5px;
            outline: none;
            background-color: #55f;
            color: white;
        }
        .submit{
            background-color: #55f;
            width: 100%;
            padding: 10px;
            border: none;
            color: white;
            outline: none;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            transition: 0.5s;
        }
        .submit:hover{
            background-color: rgb(68, 68, 202);
        }
        .submit2{
            background-color: #55f;
            border: none;
            padding: 12px;
            margin-left: 25%;
            width: 50%;
            border-radius: 10px;
            color: white;
            font-size: 13px;
            cursor: pointer; /* cursor de mãozinha ao colocar o mouse encima*/
        }
        .submit2:hover{
            background-color: rgb(68, 68, 202);
        }

    </style>
</head>
<body>
    <div class="box">
        <form action="cadastrogame.php" method="POST">
            <fieldset>
                <legend><b>Formulário de cadastro</b></legend>
                <br>
                <div class="inputBox">
                    <input type="text" name="nome" id="nome" class="inputUser" required>
                    <label for="nome" class="labelInput">Nome Completo</label>
                </div>
                <br>
                <div class="inputBox">
                    <label for="nasc">Data de nascimento:</label>
                    <input type="date" name="nasc" id="nasc" required> 
                </div>

                <p>Sexo:</p>
                <input type="radio" id="feminino" name="sexo" value="Feminino" required>
                <label for="feminino">Feminino</label>
                <input type="radio" id="Masculino" name="sexo" value="Masculino" required>
                <label for="Masculino">Masculino</label>
                <input type="radio" id="outros" name="sexo" value="Outros" required>
                <label for="outros">Outros</label>

                <br>
                <br>
                <div class="inputBox">
                    <input type="text" name="email" id="email" class="inputUser" required>
                    <label for="email" class="labelInput">Email</label>
                    
                </div>
                <br>
                <div class="inputBox">
                    <input type="text" name="nickname" id="nickname" class="inputUser" required>
                    <label for="nickname" class="labelInput">Nickname</label>
                </div>
                <br>
                <div class="inputBox">
                    <input type="password" name="senha" id="senha" class="inputUser" required>
                    <label for="senha" class="labelInput">Senha</label>
                </div>
                <br>
                <input type="submit" name="submit" id="submit" class="submit" value="Cadastrar">
                
            </fieldset>
        </form>
        <hr>
        <a href="logingame.php"><button class="submit2">Logar</button></a>
        
    </div>
    
</body>
</html>