<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

ngaged_bootstrap_admin_from_env();
$admin = ngaged_current_admin();
if ($admin === null && !ngaged_legacy_admin_key_valid()) {
    gaggle_demo_json_response(401, ['ok' => false, 'loginRequired' => true]);
}

$payload = [
    'ok' => true,
    'googleLoginAvailable' => ngaged_google_oauth_configured(),
];
if ($admin !== null) {
    $payload['admin'] = ngaged_admin_public($admin);
    $payload['auth'] = 'session';
} else {
    $payload['auth'] = 'legacyKey';
    $payload['admin'] = [
        'email' => '',
        'name' => 'API (clave legacy)',
        'role' => 'admin',
        'canManagePanelAccess' => true,
        'canManageMembers' => true,
    ];
}

gaggle_demo_json_response(200, $payload);
