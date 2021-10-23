<?php
    require 'includes/header.php';
    include('includes/conexao.php');
    $sql = "SELECT nicknamep,pontos FROM ranking ORDER BY pontos desc";
    $resultado = mysqli_query($con, $sql);
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <table>
        <tr>
            <td>Nickname</td>
            <td>Pontuação</td>
        </tr>
        <?php while($dados = mysqli_fetch_array($resultado)){ ?>
        <tr>
            <td><?php echo $dados['nicknamep']; ?></td>
            <td><?php echo $dados['pontos']; ?></td>
        </tr>
        <?php } ?>
    </table>
</body>
</html>