<?php
include 'config/auth.php';
sessionVerif();

function rankingRows(): array
{
    global $pdo;
    $sql = $pdo->prepare(
        'SELECT u.usuario, s.wins, s.losses, s.disconnects
         FROM player_stats s
         JOIN usuario u ON u.id = s.user_id
         ORDER BY s.wins DESC, s.losses ASC
         LIMIT 100'
    );
    $sql->execute();
    return $sql->fetchAll();
}

$rows = rankingRows();
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dekership - Ranking</title>
    <link rel="stylesheet" href="web/assets/tailwind.css">
    <link rel="stylesheet" href="web/ranking/ranking.css">
</head>
<body>
<?php include 'header.php'; ?>
<div class="container">
    <div class="card">
        <h2>Ranking 1v1</h2>
        <table class="table">
            <thead>
                <tr>
                    <th>Jogador</th>
                    <th>Vitórias</th>
                    <th>Derrotas</th>
                    <th>Desconexões</th>
                </tr>
            </thead>
            <tbody>
                <?php if (!$rows): ?>
                    <tr><td colspan="4">Sem dados.</td></tr>
                <?php else: ?>
                    <?php foreach ($rows as $row): ?>
                        <tr>
                            <td><?= htmlspecialchars($row['usuario']) ?></td>
                            <td><?= (int)$row['wins'] ?></td>
                            <td><?= (int)$row['losses'] ?></td>
                            <td><?= (int)$row['disconnects'] ?></td>
                        </tr>
                    <?php endforeach; ?>
                <?php endif; ?>
            </tbody>
        </table>
    </div>
</div>
</body>
</html>