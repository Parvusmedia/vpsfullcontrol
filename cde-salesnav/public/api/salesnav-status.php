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

cde_salesnav_refresh_auth_cookie();

$userId = cde_salesnav_user_id();
$stored = cde_salesnav_load_accounts()[$userId] ?? null;
$account = cde_salesnav_ensure_account_valid($userId);
$connected = $account !== null && ($account['account_id'] ?? '') !== '';
$needsReconnect = is_array($stored) && !empty($stored['invalid_at']);
$hadLink = is_array($stored) && (!empty($stored['account_id']) || !empty($stored['label']));

$unipileSeatId = '';
if ($connected) {
    $unipileSeatId = trim((string) ($account['account_id'] ?? ''));
} else {
    $seat = cde_salesnav_find_reconnectable_seat($userId);
    if ($seat !== null) {
        $unipileSeatId = $seat;
    }
}

$previousUnipileId = '';
if (is_array($stored)) {
    $prev = trim((string) ($stored['previous_account_id'] ?? ''));
    $storedId = trim((string) ($stored['account_id'] ?? ''));
    if ($prev !== '' && $prev !== $unipileSeatId) {
        $previousUnipileId = $prev;
    } elseif ($storedId !== '' && $storedId !== $unipileSeatId && !cde_salesnav_is_account_alive($storedId)) {
        $previousUnipileId = $storedId;
    }
}

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
    'unipile_account_id' => $unipileSeatId,
    'previous_unipile_account_id' => $previousUnipileId,
]);
