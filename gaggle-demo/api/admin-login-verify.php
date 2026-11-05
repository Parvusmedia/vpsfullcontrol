<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_2fa.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$loginToken = trim((string) ($input['loginToken'] ?? ''));
$code = (string) ($input['code'] ?? '');

$result = ngaged_complete_login_2fa($loginToken, $code);
if (!$result['ok']) {
    gaggle_demo_json_response(401, $result);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'admin' => $result['admin'],
]);
