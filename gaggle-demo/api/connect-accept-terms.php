<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';
require_once __DIR__ . '/_legal.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
$token = trim((string) ($input['token'] ?? ''));
$accept = (bool) ($input['accept'] ?? false);
$version = trim((string) ($input['version'] ?? ''));

if (!$accept) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Debes marcar la casilla de aceptación.']);
}

if ($version !== '' && $version !== ngaged_connect_terms_version()) {
    gaggle_demo_json_response(409, [
        'ok' => false,
        'error' => 'Las condiciones han cambiado. Recarga la página y vuelve a leerlas.',
        'terms' => ngaged_terms_acceptance_meta(),
    ]);
}

$verified = ngaged_verify_member_connect_token($token);
if ($verified === null) {
    gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
}

$result = ngaged_record_terms_acceptance($verified['memberId']);
if (!$result['ok']) {
    gaggle_demo_json_response(404, $result);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'termsAccepted' => true,
    'terms' => ngaged_terms_acceptance_meta(),
]);
