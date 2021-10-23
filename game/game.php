<?php
    require 'includes/header.php';
    if(isset($_POST['btnSalvar'])){
        include('includes/conexao.php');
        $nick = $_POST['nick'];
        $pontuacao = $_POST['pontuacao'];
        if($pontuacao >= 10){
            $result2 = mysqli_query($con, "INSERT INTO ranking (nicknamep,pontos) VALUES ('$nick','$pontuacao')");
            echo "Pontuação salva no ranking!"; 
        } else {
            echo "Serão salvas somente pontuações a partir de 10!";
        }
    }
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game</title>
    <link rel="stylesheet" href="css/estilogame.css">
    <script type="text/javascript" src="js/jscript.js"></script>
    <style>
        input{
            background: transparent;
            border: none;
            outline: none;
        }
    </style>
</head>
<body>
    <div class="conteiner">

        <!--HEADER-------------------------------->
        <div class="header">
            <h1>Dekership </h1>
            <p>Controles: Setas ou AWSD e ESPAÇO</p>
        </div>
        <!--LATERAL1-------------------------------->
        <div class="lateral1">
        
        </div>
        <!--PRINCIPAL-------------------------------->
        <div class="principal" id="omg">

            <div id="painel" class="painel">
                Planeta
                <div id="medidorPlaneta">
                    <div id="barraPlaneta"></div>
                </div>

                <form action="game.php" method="POST">
                    <label for="nick">Jogador: </label>
                    <input id="nick" width="10pt" name="nick" readonly="readonly" value="<?php echo $dados['nickname'];?>"></input>
                    <br>
                    <label for="pontuacao">Pontuação: </label>
                    <input id="pontuacao" width="10px" name="pontuacao" readonly="readonly"></input>
                    <br>
                    <p>Se não clicar em salvar a pontuação será perdida
                    <br> sem ser salva no ranking!</p>
                    <button type="submit" name="btnSalvar">  Salvar e zerar </button>
                    <div id="contBombas"></div>
                </form>
            </div>

            <div id="telaMsg" class="telaMsg">
                <p id="telaMsgTxt"></p>
                <button id="btnJogar" class="btnJogar">JOGAR</button>
            </div>

            <div id="naveJog" class="navJog"></div>
            <audio src="audio/tiro.wav" id="tiro"></audio>
            
        </div>
        <!--LATERAL2-------------------------------->
        <div class="lateral2">
            
        </div>
        <!--FOOTER-------------------------------->
        <div class="footer">
        </div>

    </div>
</body>
</html>