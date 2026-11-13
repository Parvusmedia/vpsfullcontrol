<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';
require_once __DIR__ . '/_legal.php';
require_once __DIR__ . '/_members_util.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$token = trim((string) ($input['token'] ?? ''));
$verified = ngaged_verify_member_connect_token($token);
if ($verified === null) {
    gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
}

$store = ngaged_members_store();
$found = ngaged_find_member($store, $verified['memberId']);
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Invitación no encontrada.']);
}

$member = $found['member'];
$i = $found['index'];

if (!ngaged_member_terms_accepted($member)) {
    gaggle_demo_json_response(403, [
        'ok' => false,
        'error' => 'Acepta las condiciones antes de continuar.',
        'termsRequired' => true,
    ]);
}

$provision = ngaged_provision_member_connect($member);
if (!$provision['ok']) {
    gaggle_demo_json_response(502, [
        'ok' => false,
        'error' => ngaged_user_error_message(
            $provision['error'] ?? null,
            'No pudimos preparar la autorización de LinkedIn. Inténtalo más tarde.'
        ),
        'selfConnectAvailable' => false,
    ]);
}

$member = $provision['member'];
$store['members'][$i] = $member;
ngaged_save_members($store);

$oauthUrl = trim((string) ($member['linkedinConnectUrl'] ?? ''));
$selfConnect = $oauthUrl !== '' && gaggle_publora_employee_connect_ready();

if (!$selfConnect) {
    gaggle_demo_json_response(200, [
        'ok' => true,
        'selfConnectAvailable' => false,
        'linkedinConnectUrl' => null,
        'message' => 'La autorización directa de LinkedIn no está disponible todavía. Contacta con tu administrador Ngaged.',
        'noticeCode' => 'self_connect_unavailable',
    ]);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'selfConnectAvailable' => true,
    'linkedinConnectUrl' => $oauthUrl,
    'name' => $member['name'] ?? '',
    'email' => $member['email'] ?? '',
    'message' => 'Abre LinkedIn, autoriza la conexión y vuelve aquí para confirmar.',
]);
