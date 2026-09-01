<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$userId = cde_salesnav_user_id();
$stored = cde_salesnav_load_accounts()[$userId] ?? null;
$account = cde_salesnav_ensure_account_valid($userId);
$connected = $account !== null && ($account['account_id'] ?? '') !== '';
$needsReconnect = is_array($stored) && !empty($stored['invalid_at']);
$hadLink = is_array($stored) && (!empty($stored['account_id']) || !empty($stored['label']));

cde_json_response(200, [
    'ok' => true,
    'connected' => $connected,
    'label' => $connected ? ($account['label'] ?? '') : '',
    'avatar_url' => $connected ? ($account['avatar_url'] ?? '') : '',
    'connected_at' => $connected ? ($account['connected_at'] ?? '') : '',
    'needs_reconnect' => $needsReconnect,
    'reconnect_available' => !$connected && $hadLink,
    'stored_label' => !$connected && $hadLink ? (string) ($stored['label'] ?? '') : '',
    'connect_message' => $needsReconnect ? cde_salesnav_stale_account_message() : '',
]);
