<?php
declare(strict_types=1);

/**
 * Admin credit grants (for Django ops panel or scripts).
 * POST JSON: { "email": "user@co.com", "credits": 200, "note": "optional", "ref": "optional-idempotency-key" }
 * Auth: header X-Salesnav-Admin-Token or query token= (SALESNAV_ADMIN_SECRET in private/cde/unipile.env)
 */
require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_customers.php';
require __DIR__ . '/_credits.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Salesnav-Admin-Token');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

function cde_salesnav_admin_secret(): string
{
    $env = cde_unipile_read_env();
    return trim((string) ($env['SALESNAV_ADMIN_SECRET'] ?? getenv('SALESNAV_ADMIN_SECRET') ?: ''));
}

$expected = cde_salesnav_admin_secret();
$token = trim((string) ($_SERVER['HTTP_X_SALESNAV_ADMIN_TOKEN'] ?? $_GET['token'] ?? ''));
if ($expected === '' || $token === '' || !hash_equals($expected, $token)) {
    cde_json_response(403, ['ok' => false, 'error' => 'Forbidden']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
}

$email = cde_customer_normalize_email((string) ($payload['email'] ?? ''));
$amount = (int) ($payload['credits'] ?? $payload['amount'] ?? 0);
$note = trim((string) ($payload['note'] ?? ''));
$ref = trim((string) ($payload['ref'] ?? ''));

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Valid email is required.']);
}
if ($amount <= 0 || $amount > 500000) {
    cde_json_response(400, ['ok' => false, 'error' => 'Credits must be between 1 and 500000.']);
}

$userId = cde_salesnav_user_id_for_email($email);
$before = cde_credits_get_balance($userId);
if ($ref === '') {
    $ref = 'admin:grant:' . hash('sha256', $email . '|' . $amount . '|' . gmdate('Y-m-d\TH:i:s') . '|' . bin2hex(random_bytes(8)));
}
$meta = ['email' => $email, 'source' => 'salesnav-admin-credits'];
if ($note !== '') {
    $meta['note'] = $note;
}

$after = cde_credits_add($userId, $amount, $ref, $meta);

cde_json_response(200, [
    'ok' => true,
    'email' => $email,
    'user_id' => $userId,
    'granted' => $amount,
    'balance_before' => $before,
    'balance' => $after,
    'ref' => $ref,
]);
