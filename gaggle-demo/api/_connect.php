<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_publora.php';
require_once __DIR__ . '/_tokens.php';
require_once __DIR__ . '/_members_util.php';

function ngaged_member_connect_token(string $memberId, int $ttlSeconds = 2592000): string
{
    $payload = [
        'm' => $memberId,
        't' => 'connect',
        'e' => time() + $ttlSeconds,
    ];
    $json = json_encode($payload, JSON_UNESCAPED_SLASHES);
    $b64 = rtrim(strtr(base64_encode($json), '+/', '-_'), '=');
    $sig = hash_hmac('sha256', $b64, ngaged_signing_secret());
    return $b64 . '.' . $sig;
}

/** @return array{memberId:string}|null */
function ngaged_verify_member_connect_token(string $token): ?array
{
    $token = trim($token);
    if ($token === '' || !str_contains($token, '.')) {
        return null;
    }
    [$b64, $sig] = explode('.', $token, 2);
    $expected = hash_hmac('sha256', $b64, ngaged_signing_secret());
    if (!hash_equals($expected, $sig)) {
        return null;
    }
    $pad = strlen($b64) % 4;
    if ($pad) {
        $b64 .= str_repeat('=', 4 - $pad);
    }
    $json = base64_decode(strtr($b64, '-_', '+/'), true);
    if ($json === false) {
        return null;
    }
    $data = json_decode($json, true);
    if (!is_array($data) || ($data['t'] ?? '') !== 'connect' || !isset($data['m'], $data['e'])) {
        return null;
    }
    if ((int) $data['e'] < time()) {
        return null;
    }
    return ['memberId' => (string) $data['m']];
}

function ngaged_member_connect_page_url(string $token): string
{
    return ngaged_app_base_url() . '/conectar?' . http_build_query(['token' => $token]);
}

/**
 * @return array{ok:bool,member?:array,inviteUrl?:string,linkedinConnectUrl?:string,workspaceEnabled?:bool,error?:string}
 */
function ngaged_provision_member_connect(array $member): array
{
    $email = (string) ($member['email'] ?? '');
    $name = (string) ($member['name'] ?? $email);
    $token = ngaged_member_connect_token((string) ($member['id'] ?? ''));
    $inviteUrl = ngaged_member_connect_page_url($token);

    $member['inviteUrl'] = $inviteUrl;
    $member['connectStatus'] = $member['connectStatus'] ?? 'pending';

    if (!gaggle_publora_workspace_enabled()) {
        $member['workspaceEnabled'] = false;
        return [
            'ok' => true,
            'member' => $member,
            'inviteUrl' => $inviteUrl,
            'linkedinConnectUrl' => null,
            'workspaceEnabled' => false,
            'notice' => 'OAuth LinkedIn directo no está activo: envía solo el enlace Ngaged o vincula la cuenta en Miembros.',
        ];
    }

    $publoraUserId = trim((string) ($member['publoraUserId'] ?? ''));
    if ($publoraUserId === '') {
        $created = gaggle_publora_create_managed_user($email, $name);
        if (!$created['ok']) {
            return ['ok' => false, 'error' => $created['error'] ?? 'No se pudo crear usuario gestionado.'];
        }
        $publoraUserId = $created['userId'];
        $member['publoraUserId'] = $publoraUserId;
    }

    $link = gaggle_publora_connection_url($publoraUserId);
    if (!$link['ok'] || ($link['url'] ?? '') === '') {
        return ['ok' => false, 'error' => $link['error'] ?? 'No se pudo generar el enlace de conexión.'];
    }

    $member['linkedinConnectUrl'] = $link['url'];
    $member['connectUrlExpiresAt'] = $link['tokenExpiresAt'] ?? null;
    $member['workspaceEnabled'] = true;
    $member['connectStatus'] = 'invited';

    return [
        'ok' => true,
        'member' => $member,
        'inviteUrl' => $inviteUrl,
        'linkedinConnectUrl' => $link['url'],
        'workspaceEnabled' => true,
    ];
}

function ngaged_sync_member_linkedin(string $memberId): array
{
    $store = ngaged_members_store();
    $found = ngaged_find_member($store, $memberId);
    if ($found === null) {
        return ['ok' => false, 'error' => 'Miembro no encontrado.'];
    }
    $i = $found['index'];
    $member = $found['member'];
    $publoraUserId = trim((string) ($member['publoraUserId'] ?? ''));
    if ($publoraUserId === '') {
        return ['ok' => false, 'error' => 'Este miembro aún no tiene usuario de conexión. Genera el enlace primero.'];
    }
    $li = gaggle_publora_first_linkedin_for_user($publoraUserId);
    if (!$li['ok']) {
        return $li;
    }
    $member['platformId'] = $li['platformId'];
    $member['connectStatus'] = 'pending_review';
    $member['linkedAt'] = gmdate('c');
    unset($member['approvedAt'], $member['approvedBy']);
    $store['members'][$i] = $member;
    ngaged_save_members($store);
    return [
        'ok' => true,
        'member' => $member,
        'platformId' => $li['platformId'],
        'awaitingAdminApproval' => true,
    ];
}
