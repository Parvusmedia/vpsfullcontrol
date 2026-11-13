<?php

declare(strict_types=1);

require_once __DIR__ . '/_publora_company.php';

function ngaged_member_publora_credential_id(array &$member): string
{
    $existing = strtolower(trim((string) ($member['publoraCredentialId'] ?? '')));
    if (preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/', $existing)) {
        return $existing;
    }

    $legacy = strtolower(trim((string) ($member['publoraUserId'] ?? '')));
    if (preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/', $legacy)) {
        $member['publoraCredentialId'] = $legacy;
        return $legacy;
    }

    $bytes = random_bytes(16);
    $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
    $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
    $hex = bin2hex($bytes);
    $uuid = sprintf(
        '%s-%s-%s-%s-%s',
        substr($hex, 0, 8),
        substr($hex, 8, 4),
        substr($hex, 12, 4),
        substr($hex, 16, 4),
        substr($hex, 20, 12)
    );
    $member['publoraCredentialId'] = $uuid;
    return $uuid;
}

/**
 * @return array{ok:bool,member?:array,linkedinConnectUrl?:string,error?:string,code?:string}
 */
function ngaged_provision_member_connect_company(array $member): array
{
    if (!gaggle_publora_company_context_ok()) {
        return [
            'ok' => false,
            'error' => 'Ngaged no tiene acceso al workspace de conexión. Revisa PUBLORA_WORKSPACE_ID en el servidor.',
        ];
    }

    $credentialId = ngaged_member_publora_credential_id($member);
    $link = gaggle_publora_company_connection_link($credentialId);
    if (!$link['ok']) {
        return [
            'ok' => false,
            'error' => $link['error'] ?? 'No se pudo generar el enlace de conexión.',
            'code' => $link['code'] ?? null,
        ];
    }

    $member['linkedinConnectUrl'] = $link['url'];
    $member['companyConnectEnabled'] = true;
    $member['connectStatus'] = $member['connectStatus'] ?? 'invited';

    return [
        'ok' => true,
        'member' => $member,
        'linkedinConnectUrl' => $link['url'],
    ];
}

/** @return array{ok:bool,member?:array,platformId?:string,awaitingAdminApproval?:bool,error?:string} */
function ngaged_sync_member_linkedin_company(string $memberId): array
{
    $store = ngaged_members_store();
    $found = ngaged_find_member($store, $memberId);
    if ($found === null) {
        return ['ok' => false, 'error' => 'Miembro no encontrado.'];
    }
    $i = $found['index'];
    $member = $found['member'];

    $credentialId = ngaged_member_publora_credential_id($member);
    $li = gaggle_publora_company_linkedin_for_credential($credentialId);
    if (!$li['ok']) {
        return $li;
    }

    $member['platformId'] = $li['platformId'];
    if (isset($li['connectionId']) && $li['connectionId'] !== '') {
        $member['publoraConnectionId'] = $li['connectionId'];
    }
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
