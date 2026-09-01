<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_credits.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$ip = cde_client_ip();
$check = cde_rate_consume('salesnav_connect_ip_hour', $ip, 10, 3600);
if (!$check['ok']) {
    cde_json_response(429, [
        'ok' => false,
        'error' => 'Too many connection attempts. Try again later.',
        'retry_after' => $check['retry_after'],
    ]);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = [];
}

$userId = cde_salesnav_user_id();
$stored = cde_salesnav_load_accounts()[$userId] ?? null;
$sessionAccount = cde_salesnav_session_account();
$explicitReconnect = !empty($payload['reconnect']);
$storedInvalid = is_array($stored) && !empty($stored['invalid_at']);
$storedAlive = is_array($stored)
    && !empty($stored['account_id'])
    && !$storedInvalid
    && cde_salesnav_is_account_alive((string) $stored['account_id']);
$hadPriorLink = is_array($stored) && (!empty($stored['account_id']) || !empty($stored['label']));

if ($storedAlive) {
    $type = 'reconnect';
    $reconnectId = (string) $stored['account_id'];
} elseif ($explicitReconnect && $sessionAccount !== null && ($sessionAccount['account_id'] ?? '') !== '') {
    $accountId = (string) $sessionAccount['account_id'];
    if (cde_salesnav_is_account_alive($accountId)) {
        $type = 'reconnect';
        $reconnectId = $accountId;
    } else {
        $type = 'create';
        $reconnectId = null;
    }
} else {
    $resolved = cde_salesnav_resolve_linked_account_id($userId);
    if ($resolved !== null && cde_salesnav_is_account_alive($resolved)) {
        $type = 'reconnect';
        $reconnectId = $resolved;
    } else {
        if (!$hadPriorLink && !$explicitReconnect) {
            cde_credits_require_positive_balance();
        }
        $type = 'create';
        $reconnectId = null;
    }
}

$result = cde_salesnav_create_hosted_link($type, $reconnectId);

cde_json_response(200, [
    'ok' => true,
    'url' => $result['url'],
    'type' => $type,
    'reused_account' => $type === 'reconnect',
]);
