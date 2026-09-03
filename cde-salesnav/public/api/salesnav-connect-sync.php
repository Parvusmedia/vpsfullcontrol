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
$stored = cde_salesnav_load_accounts()[$userId] ?? null;
$accountId = cde_salesnav_find_syncable_seat($userId);

if ($accountId === null) {
    if (!is_array($stored)) {
        cde_json_response(404, [
            'ok' => false,
            'error' => 'No LinkedIn account linked to this panel yet.',
        ]);
    }
    cde_json_response(404, [
        'ok' => false,
        'error' => 'LinkedIn connection not ready yet. Try again in a moment.',
        'retry' => true,
    ]);
}

if (!cde_salesnav_is_account_alive($accountId)) {
    cde_json_response(404, [
        'ok' => false,
        'error' => 'LinkedIn connection not ready yet. Try again in a moment.',
        'retry' => true,
        'account_id' => $accountId,
    ]);
}

try {
    $meta = cde_salesnav_apply_unipile_account($userId, $accountId);
} catch (RuntimeException $e) {
    cde_json_response(409, [
        'ok' => false,
        'error' => $e->getMessage(),
        'account_id' => $accountId,
    ]);
}
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
