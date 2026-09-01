<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';

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

if (!cde_salesnav_is_account_alive($accountId)) {
    cde_json_response(502, [
        'ok' => false,
        'error' => 'Unipile account is not ready yet.',
    ]);
}

$existing = cde_salesnav_load_accounts()[$userId] ?? [];
if (!is_array($existing)) {
    $existing = [];
}
$previous = trim((string) ($existing['account_id'] ?? ''));
if ($previous !== '' && $previous !== $accountId) {
    $metaPreview = cde_salesnav_fetch_account_meta(cde_unipile_api_config($accountId), $accountId);
    cde_salesnav_propagate_account_id($previous, $accountId, $metaPreview);
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
cde_salesnav_save_account($userId, array_merge(cde_salesnav_load_accounts()[$userId] ?? [], [
    'status' => $status,
]));

cde_json_response(200, [
    'ok' => true,
    'account_id' => $accountId,
    'previous_account_id' => $previous !== '' && $previous !== $accountId ? $previous : null,
    'label' => $meta['label'] ?? '',
]);
