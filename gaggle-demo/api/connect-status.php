<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

$token = trim((string) ($_GET['token'] ?? ''));
$verified = ngaged_verify_member_connect_token($token);
if ($verified === null) {
    gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
}

$found = ngaged_find_member(ngaged_members_store(), $verified['memberId']);
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Invitación no encontrada.']);
}

$member = $found['member'];
gaggle_demo_json_response(200, [
    'ok' => true,
    'name' => $member['name'] ?? '',
    'email' => $member['email'] ?? '',
    'linkedinConnectUrl' => $member['linkedinConnectUrl'] ?? null,
    'platformLinked' => trim((string) ($member['platformId'] ?? '')) !== '',
    'connectStatus' => $member['connectStatus'] ?? 'pending',
    'workspaceEnabled' => (bool) ($member['workspaceEnabled'] ?? gaggle_publora_workspace_enabled()),
]);
