<?php
include("config/auth.php");
global $pdo;
sessionVerif();

function tabelaRanking()
{
    global $pdo;
    $sql = $pdo->prepare("SELECT * FROM ranking ORDER BY pontuacao desc");
    $sql->execute();
    while ($row = $sql->fetch(PDO::FETCH_ASSOC)) {
        $data = $row['dataRanking'];
        $dataf = new DateTime($data);
        $dataf = $dataf->format('d/m/Y H:i:s');

        echo "<tr>";
        echo "<td>" . $row['usuario'] . "</td>";
        echo "<td>" . $row['pontuacao'] . "</td>";
        echo "<td> $dataf </td>";
    }
}
?>
<!DOCTYPE html>
<html lang="pt-br">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dekership : Ranking</title>
    <link rel="stylesheet" href="css/datatable.css">
    <link rel="stylesheet" href="web/ranking/ranking.css">
</head>

<body>
    <?php include 'header.php'; ?>
    <main class="main">
        <div class="div-tabela">
            <table id="tabela-ranking">
                <thead>
                    <td>Jogador</td>
                    <td>Pontuação</td>
                    <td>Data</td>
                </thead>
                <tbody>
                    <?php tabelaRanking(); ?>
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>

<!--Datatable Dependências-->
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<script src="js/datatable.js"></script>
<!-- Datatable - Tabela -->
<script src="web/ranking/ranking.js"></script>