<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
$token = trim((string) ($input['token'] ?? $_GET['token'] ?? ''));
$verified = ngaged_verify_member_connect_token($token);
if ($verified === null) {
    gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
}

$result = ngaged_sync_member_linkedin($verified['memberId']);
if (!$result['ok']) {
    gaggle_demo_json_response(422, ['ok' => false, 'error' => $result['error'] ?? 'Aún no detectamos LinkedIn.']);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'message' => 'LinkedIn vinculado correctamente.',
    'platformId' => $result['platformId'] ?? null,
]);
