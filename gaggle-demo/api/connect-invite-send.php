<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';
require_once __DIR__ . '/_members_util.php';
require_once __DIR__ . '/_mail.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_full_admin();
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
    $found = ngaged_find_member_by_email($store, $email);
    if ($found !== null) {
        $member = $found['member'];
        $idx = $found['index'];
        $newName = trim((string) ($input['name'] ?? ''));
        if ($newName !== '') {
            $member['name'] = $newName;
        }
    } else {
        $member = [
            'id' => gaggle_demo_new_id('mem'),
            'name' => trim((string) ($input['name'] ?? '')),
            'email' => $email,
            'platformId' => '',
            'teamId' => '',
            'createdAt' => gmdate('c'),
        ];
        $idx = count($members);
        $members[] = $member;
    }
}

$inviteUrl = trim((string) ($member['inviteUrl'] ?? ''));
if ($inviteUrl === '') {
    $result = ngaged_provision_member_connect($member);
    if (!$result['ok']) {
        gaggle_demo_json_response(502, ['ok' => false, 'error' => ngaged_user_error_message($result['error'] ?? null)]);
    }
    $member = $result['member'];
    $inviteUrl = (string) ($result['inviteUrl'] ?? '');
}

if ($inviteUrl === '') {
    gaggle_demo_json_response(502, ['ok' => false, 'error' => 'No se pudo generar el enlace de invitación.']);
}

$email = strtolower(trim((string) ($member['email'] ?? '')));
if ($email === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'El miembro no tiene email.']);
}

$name = trim((string) ($member['name'] ?? ''));
$subject = ngaged_connect_invite_email_subject();
$html = ngaged_connect_invite_email_html($name, $inviteUrl);
$text = ngaged_connect_invite_email_text($name, $inviteUrl);
$sent = ngaged_send_mail_verbose($email, $subject, $html, $text);

if (!$sent['ok']) {
    $hint = $sent['error'] ? ' (' . ngaged_user_error_message($sent['error']) . ')' : '';
    gaggle_demo_json_response(502, ['ok' => false, 'error' => 'No se pudo enviar el email de invitación.' . $hint]);
}

$member['connectStatus'] = 'invited';
$member['inviteSentAt'] = gmdate('c');
$members[$idx] = $member;
$store['members'] = $members;
ngaged_save_members($store);

gaggle_demo_json_response(200, [
    'ok' => true,
    'mailSent' => true,
    'to' => $email,
    'inviteUrl' => $inviteUrl,
    'member' => $member,
    'transport' => $sent['transport'] ?? null,
]);
