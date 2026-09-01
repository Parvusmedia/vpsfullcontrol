<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_customers.php';
require __DIR__ . '/_stripe.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

if (!cde_credits_billing_enabled()) {
    cde_json_response(503, [
        'ok' => false,
        'error' => 'Billing is not enabled yet.',
    ]);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = [];
}

$packId = (string) ($payload['pack'] ?? '240');
$auth = cde_salesnav_require_auth();
$email = $auth['email'];
$userId = $auth['user_id'];
$result = cde_stripe_create_checkout_session($userId, $packId, $email);

cde_json_response(200, [
    'ok' => true,
    'url' => $result['url'],
    'session_id' => $result['session_id'],
    'credits' => $result['credits'],
]);
