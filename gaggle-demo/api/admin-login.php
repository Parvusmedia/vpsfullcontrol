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

$email = strtolower(trim((string) ($input['email'] ?? '')));
$password = (string) ($input['password'] ?? '');
if ($email === '' || $password === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email y contraseña obligatorios.']);
}

$check = ngaged_verify_admin_password($email, $password);
if (!$check['ok']) {
    gaggle_demo_json_response(401, $check);
}

$admin = $check['admin'];

if (!ngaged_admin_2fa_enabled()) {
    ngaged_establish_admin_session($admin);
    gaggle_demo_json_response(200, [
        'ok' => true,
        'admin' => ngaged_admin_public($admin),
    ]);
}

$started = ngaged_start_login_2fa($admin);
if (!$started['ok']) {
    gaggle_demo_json_response(502, $started);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'requires2fa' => true,
    'loginToken' => $started['loginToken'],
    'emailMasked' => $started['emailMasked'],
    'message' => 'Te hemos enviado un código de 6 dígitos por email.',
]);
