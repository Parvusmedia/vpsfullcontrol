<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

ngaged_logout_admin();
gaggle_demo_json_response(200, ['ok' => true]);
