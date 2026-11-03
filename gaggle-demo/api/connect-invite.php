<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_admin();
$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$memberId = trim((string) ($input['memberId'] ?? ''));
$store = ngaged_members_store();
$members = $store['members'] ?? [];

if ($memberId !== '') {
    $found = ngaged_find_member($store, $memberId);
    if ($found === null) {
        gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Miembro no encontrado.']);
    }
    $member = $found['member'];
    $idx = $found['index'];
} else {
    $email = strtolower(trim((string) ($input['email'] ?? '')));
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email válido obligatorio.']);
    }
    foreach ($members as $m) {
        if (is_array($m) && strtolower((string) ($m['email'] ?? '')) === $email) {
            gaggle_demo_json_response(409, ['ok' => false, 'error' => 'Ese email ya existe. Usa Regenerar enlace.']);
        }
    }
    $member = [
        'id' => gaggle_demo_new_id('mem'),
        'name' => trim((string) ($input['name'] ?? '')),
        'email' => $email,
        'platformId' => '',
        'createdAt' => gmdate('c'),
    ];
    $idx = count($members);
    $members[] = $member;
}

$result = ngaged_provision_member_connect($member);
if (!$result['ok']) {
    gaggle_demo_json_response(502, ['ok' => false, 'error' => $result['error'] ?? 'Error']);
}

$member = $result['member'];
$members[$idx] = $member;
ngaged_save_members(['members' => $members]);

gaggle_demo_json_response(200, [
    'ok' => true,
    'member' => $member,
    'inviteUrl' => $result['inviteUrl'],
    'linkedinConnectUrl' => $result['linkedinConnectUrl'] ?? null,
    'workspaceEnabled' => $result['workspaceEnabled'] ?? false,
    'notice' => $result['notice'] ?? null,
]);
