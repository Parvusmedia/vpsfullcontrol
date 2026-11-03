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
$i = $found['index'];
$store = ngaged_members_store();

if (gaggle_publora_workspace_enabled()) {
    $provision = ngaged_provision_member_connect($member);
    if ($provision['ok'] && isset($provision['member']) && is_array($provision['member'])) {
        $member = $provision['member'];
        $store['members'][$i] = $member;
        ngaged_save_members($store);
    }
}

$oauthUrl = trim((string) ($member['linkedinConnectUrl'] ?? ''));
if ($oauthUrl === '') {
    $oauthUrl = null;
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'name' => $member['name'] ?? '',
    'email' => $member['email'] ?? '',
    'linkedinConnectUrl' => $oauthUrl,
    'platformLinked' => trim((string) ($member['platformId'] ?? '')) !== '',
    'connectStatus' => $member['connectStatus'] ?? 'pending',
    'selfConnectAvailable' => $oauthUrl !== null,
    'workspaceEnabled' => (bool) ($member['workspaceEnabled'] ?? gaggle_publora_workspace_enabled()),
]);
