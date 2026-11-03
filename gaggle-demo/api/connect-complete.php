<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';
require_once __DIR__ . '/_legal.php';

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

$found = ngaged_find_member(ngaged_members_store(), $verified['memberId']);
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Invitación no encontrada.']);
}

$member = $found['member'];
$termsBlock = ngaged_require_terms_accepted($member);
if ($termsBlock !== null) {
    gaggle_demo_json_response(403, $termsBlock);
}

$existing = trim((string) ($member['platformId'] ?? ''));
if ($existing !== '') {
    gaggle_demo_json_response(200, [
        'ok' => true,
        'message' => 'LinkedIn vinculado correctamente.',
        'platformId' => $existing,
    ]);
}

$result = ngaged_sync_member_linkedin($verified['memberId']);
if (!$result['ok']) {
    $hint = gaggle_publora_workspace_enabled()
        ? 'Completa la autorización en LinkedIn y vuelve a pulsar comprobar.'
        : 'Tu administrador aún no ha vinculado tu perfil. Avísale y vuelve a comprobar en unos minutos.';
    gaggle_demo_json_response(422, [
        'ok' => false,
        'error' => $result['error'] ?? 'Aún no detectamos LinkedIn.',
        'hint' => $hint,
    ]);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'message' => 'LinkedIn vinculado correctamente.',
    'platformId' => $result['platformId'] ?? null,
]);
