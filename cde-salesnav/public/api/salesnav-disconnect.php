<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_customers.php';
require __DIR__ . '/_unipile.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$userId = cde_salesnav_user_id();
$stored = cde_salesnav_stored_account($userId);
if ($stored !== null) {
    cde_salesnav_save_account($userId, array_merge($stored, [
        'disconnected_at' => gmdate('c'),
    ]));
}

cde_salesnav_clear_session_account();

cde_json_response(200, ['ok' => true, 'connected' => false]);
