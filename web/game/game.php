<?php
include("config/auth.php");
global $pdo;
sessionVerif();

if (isset($_SESSION['mensagem'])) {
    echo $_SESSION['mensagem'];
}

if (isset($_POST['submit'])) {
    $user = $_POST['usuario'];
    $pontuacao = $_POST['pontuacao'];
    if ($pontuacao > 0) {
        try {
            $data = date('Y-m-d H:i:s');

            $sql = $pdo->prepare("INSERT INTO ranking VALUES (null, ?, ?, ?)");
            $sql->execute(array($user, $pontuacao, $data));
            $_SESSION['mensagem'] = "Pontuação salva no ranking!";
        } catch (PDOException $erro) {
            $_SESSION['mensagem'] = "erro:" . $erro;
        }
    }
}
?>

<!DOCTYPE html>
<html lang="pt-br">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dekership</title>
    <link rel="stylesheet" href="web/game/game.css">
    <script type="text/javascript" src="web/game/game.js"></script>
    <style>
        input {
            background: transparent;
            border: none;
            outline: none;
        }
    </style>
</head>

<body>
    <?php include 'header.php'; ?>
    <main class="main" id="main">
        <div class="conteiner">
            <!--HEADER-------------------------------->
            <div class="header">
                <h1>Dekership </h1>
                <p>Controles: Setas ou AWSD • Tiro: Espaço • Correr: Shift pressionado</p>
            </div>
            <!--PRINCIPAL-------------------------------->
            <div class="principal" id="omg">
                <div id="painel" class="painel">
                    <p class="vida">Vida:</p>
                    <div id="medidorPlaneta">
                        <div id="barraPlaneta"></div>
                    </div>

                    <form class="form" id="meuFormulario" method="POST">
                        <div class="item-form">
                            <label for="usuario">Jogador: </label>
                            <input id="usuario" width="10pt" name="usuario" readonly="readonly"
                                value="<?php echo $usuario['usuario']; ?>"></input>
                        </div>

                        <div class="item-form">
                            <label for="pontuacao">Pontuação: </label>
                            <input id="pontuacao" width="10px" name="pontuacao" readonly="readonly"></input>
                        </div>

                        <button type="submit" name="submit" id="submitBtn"></button>
                        <div id="contBombas"></div>
                    </form>
                </div>

                <div id="telaMsg" class="telaMsg">
                    <p id="telaMsgTxt"></p>
                    <button id="btnJogar" class="btnJogar">JOGAR</button>
                </div>

                <div id="naveJog" class="navJog"></div>

            </div>

        </div>
    </main>

</body>

</html>