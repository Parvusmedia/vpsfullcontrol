<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
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
$all = cde_salesnav_load_accounts();
if (isset($all[$userId])) {
    unset($all[$userId]);
    $path = cde_salesnav_accounts_file();
    @file_put_contents($path, json_encode($all, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}

cde_salesnav_clear_session_account();

cde_json_response(200, ['ok' => true, 'connected' => false]);
