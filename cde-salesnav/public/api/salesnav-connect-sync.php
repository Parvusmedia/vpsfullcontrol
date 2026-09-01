<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$auth = cde_salesnav_require_auth();
$userId = $auth['user_id'];
$stored = cde_salesnav_stored_account($userId);
if ($stored === null || empty($stored['account_id'])) {
    cde_json_response(404, [
        'ok' => false,
        'error' => 'No LinkedIn account linked to this panel yet.',
    ]);
}

if (!empty($stored['invalid_at'])) {
    cde_json_response(403, [
        'ok' => false,
        'error' => cde_salesnav_stale_account_message(),
        'needs_reconnect' => true,
        'reconnect_available' => true,
    ]);
}

$accountId = (string) $stored['account_id'];
if (!cde_salesnav_is_account_alive($accountId)) {
    cde_salesnav_mark_account_stale($userId);
    cde_json_response(403, [
        'ok' => false,
        'error' => cde_salesnav_stale_account_message(),
        'needs_reconnect' => true,
        'reconnect_available' => true,
    ]);
}

if (!empty($stored['disconnected_at'])) {
    cde_salesnav_save_account($userId, array_merge($stored, [
        'disconnected_at' => null,
    ]));
}
$meta = cde_salesnav_refresh_account_meta($userId, $accountId);
cde_salesnav_touch_account_validated($userId);
$account = cde_salesnav_session_account();
$connected = $account !== null && ($account['account_id'] ?? '') !== '';

cde_json_response(200, [
    'ok' => true,
    'connected' => $connected,
    'label' => $connected ? ($account['label'] ?? '') : '',
    'avatar_url' => $connected ? ($account['avatar_url'] ?? '') : '',
    'connected_at' => $connected ? ($account['connected_at'] ?? '') : '',
    'account_id' => $accountId,
    'refreshed' => $meta,
]);
