<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_unipile.php';
require __DIR__ . '/_credits.php';

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

$existing = cde_salesnav_session_account();
$reconnect = !empty($payload['reconnect']) && $existing !== null;
if (!$reconnect) {
    cde_credits_require_positive_balance();
}
$type = $reconnect ? 'reconnect' : 'create';
$reconnectId = $reconnect ? (string) $existing['account_id'] : null;

$result = cde_salesnav_create_hosted_link($type, $reconnectId);

cde_json_response(200, [
    'ok' => true,
    'url' => $result['url'],
    'type' => $type,
]);
