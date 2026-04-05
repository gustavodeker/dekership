<?php

declare(strict_types=1);

function redirect_to(string $page): never
{
    header('Location: /index.php?page=' . urlencode($page));
    exit;
}

function render_header(string $title): void
{
    $user = current_user();
    require __DIR__ . '/templates/header.php';
}

function render_footer(): void
{
    require __DIR__ . '/templates/footer.php';
}
