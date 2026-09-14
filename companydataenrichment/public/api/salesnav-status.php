<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_unipile.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$account = cde_salesnav_session_account();
$connected = $account !== null && ($account['account_id'] ?? '') !== '';

if ($connected && ($account['avatar_url'] ?? '') === '') {
    $userId = cde_salesnav_user_id();
    $meta = cde_salesnav_refresh_account_meta($userId, (string) $account['account_id']);
    $account = cde_salesnav_session_account() ?? $account;
    if (($account['label'] ?? '') === '' && ($meta['label'] ?? '') !== '') {
        $account['label'] = $meta['label'];
    }
    if (($account['avatar_url'] ?? '') === '' && ($meta['avatar_url'] ?? '') !== '') {
        $account['avatar_url'] = $meta['avatar_url'];
    }
}

cde_json_response(200, [
    'ok' => true,
    'connected' => $connected,
    'label' => $connected ? ($account['label'] ?? '') : '',
    'avatar_url' => $connected ? ($account['avatar_url'] ?? '') : '',
    'connected_at' => $connected ? ($account['connected_at'] ?? '') : '',
]);
