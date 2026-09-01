<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
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

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = [];
}

$email = strtolower(trim((string) ($payload['email'] ?? '')));
$action = strtolower(trim((string) ($payload['action'] ?? 'signin')));

if ($action === 'signout') {
    cde_salesnav_sign_out_customer();
    cde_json_response(200, [
        'ok' => true,
        'signed_out' => true,
        'balance' => 0,
        'email' => '',
    ]);
}

if ($email === '') {
    cde_json_response(400, ['ok' => false, 'error' => 'Email is required.']);
}

$userId = cde_salesnav_bind_customer_email($email);
$balance = cde_credits_get_balance($userId);

cde_json_response(200, [
    'ok' => true,
    'email' => $email,
    'balance' => $balance,
    'has_credits' => $balance > 0,
]);
