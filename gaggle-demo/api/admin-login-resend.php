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
if ($loginToken === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Sesión de verificación inválida.']);
}

$store = ngaged_purge_expired_challenges(ngaged_login_challenges_store());
$row = null;
foreach ($store['challenges'] as $c) {
    if (is_array($c) && hash_equals((string) ($c['token'] ?? ''), $loginToken)) {
        $row = $c;
        break;
    }
}
if ($row === null) {
    gaggle_demo_json_response(410, ['ok' => false, 'error' => 'El código ha caducado. Vuelve a iniciar sesión.']);
}

$found = ngaged_find_admin_by_id(ngaged_admins_store(), (string) ($row['adminId'] ?? ''));
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Cuenta no encontrada.']);
}

$started = ngaged_start_login_2fa($found['admin']);
if (!$started['ok']) {
    gaggle_demo_json_response(502, $started);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'loginToken' => $started['loginToken'],
    'emailMasked' => $started['emailMasked'],
    'message' => 'Nuevo código enviado.',
]);
