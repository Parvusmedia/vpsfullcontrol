<?php
declare(strict_types=1);

/**
 * Legacy admin grant endpoint — prefer salesnav-admin-api.php?action=grant
 */
require_once __DIR__ . '/_salesnav_admin.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Salesnav-Admin-Token');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

cde_sn_admin_require_auth();

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
}

$email = (string) ($payload['email'] ?? '');
$amount = (int) ($payload['credits'] ?? $payload['amount'] ?? 0);
$note = trim((string) ($payload['note'] ?? ''));
$ref = trim((string) ($payload['ref'] ?? ''));

cde_json_response(200, cde_sn_admin_grant_credits($email, $amount, $note, $ref));
