<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$email = strtolower(trim((string) ($input['email'] ?? '')));
$password = (string) ($input['password'] ?? '');
if ($email === '' || $password === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email y contraseña obligatorios.']);
}

$result = ngaged_login_admin($email, $password);
if (!$result['ok']) {
    gaggle_demo_json_response(401, $result);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'admin' => $result['admin'],
]);
