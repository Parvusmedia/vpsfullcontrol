<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
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
    cde_json_response(503, ['ok' => false, 'error' => 'Billing is not enabled yet.']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = [];
}

$sessionId = trim((string) ($payload['session_id'] ?? $_GET['session_id'] ?? ''));
if ($sessionId === '') {
    cde_json_response(400, ['ok' => false, 'error' => 'Missing checkout session.']);
}

$resp = cde_stripe_retrieve_checkout_session($sessionId);
if (!$resp['ok']) {
    cde_json_response(502, ['ok' => false, 'error' => $resp['error'] ?? 'Could not verify payment.']);
}

$result = cde_stripe_apply_checkout_credits($resp['data'], true);
if (!$result['ok']) {
    cde_json_response(409, ['ok' => false, 'error' => $result['error'] ?? 'Payment not completed.']);
}

cde_json_response(200, [
    'ok' => true,
    'balance' => (int) ($result['balance'] ?? 0),
    'credits_added' => (int) ($result['credits'] ?? 0),
    'email' => (string) ($result['email'] ?? cde_salesnav_session_email() ?? ''),
]);
