<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

logout_user();
redirect_to('login');
