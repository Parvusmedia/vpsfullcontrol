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
$stored = cde_salesnav_stored_account($userId);
$sessionAccount = cde_salesnav_session_account();
$explicitReconnect = !empty($payload['reconnect']);

if ($stored !== null) {
    $type = 'reconnect';
    $reconnectId = (string) $stored['account_id'];
} elseif ($explicitReconnect && $sessionAccount !== null && ($sessionAccount['account_id'] ?? '') !== '') {
    $type = 'reconnect';
    $reconnectId = (string) $sessionAccount['account_id'];
} else {
    cde_credits_require_positive_balance();
    $type = 'create';
    $reconnectId = null;
}

$result = cde_salesnav_create_hosted_link($type, $reconnectId);

cde_json_response(200, [
    'ok' => true,
    'url' => $result['url'],
    'type' => $type,
    'reused_account' => $type === 'reconnect',
]);
