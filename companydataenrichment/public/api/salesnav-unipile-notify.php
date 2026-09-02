<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_unipile.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$token = trim((string) ($_GET['token'] ?? ''));
$expected = cde_salesnav_notify_secret();
if ($token === '' || !hash_equals($expected, $token)) {
    cde_json_response(403, ['ok' => false, 'error' => 'Forbidden']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid payload']);
}

$status = strtoupper(trim((string) ($payload['status'] ?? '')));
$accountId = trim((string) ($payload['account_id'] ?? ''));
$userId = trim((string) ($payload['name'] ?? ''));

if ($accountId === '' || $userId === '') {
    cde_json_response(400, ['ok' => false, 'error' => 'Missing account_id or name']);
}

if (!in_array($status, ['CREATION_SUCCESS', 'RECONNECTED'], true)) {
    cde_json_response(200, ['ok' => true, 'ignored' => true, 'status' => $status]);
}

$config = cde_unipile_api_config();
$meta = cde_salesnav_fetch_account_meta($config, $accountId);

cde_salesnav_save_account($userId, [
    'account_id' => $accountId,
    'label' => $meta['label'],
    'avatar_url' => $meta['avatar_url'],
    'status' => $status,
    'linked_at' => gmdate('c'),
]);

// If this browser session initiated the connect flow, attach immediately.
cde_session_start();
if (cde_salesnav_user_id() === $userId) {
    cde_salesnav_set_session_account($accountId, $meta['label'], $meta['avatar_url']);
}

cde_json_response(200, ['ok' => true]);
