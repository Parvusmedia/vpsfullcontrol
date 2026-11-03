<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_tokens.php';

/** Versión publicada de condiciones de vinculación Ngaged (cambiar al actualizar el texto legal). */
function ngaged_connect_terms_version(): string
{
    return '2026-11-03';
}

function ngaged_connect_terms_url(): string
{
    return ngaged_app_base_url() . '/terminos-conexion';
}

/** @param array<string,mixed> $member */
function ngaged_member_terms_accepted(array $member): bool
{
    $acc = $member['termsAcceptance'] ?? null;
    if (!is_array($acc)) {
        return false;
    }
    $ver = trim((string) ($acc['version'] ?? ''));
    $at = trim((string) ($acc['acceptedAt'] ?? ''));
    return $ver === ngaged_connect_terms_version() && $at !== '';
}

function ngaged_terms_acceptance_meta(): array
{
    return [
        'version' => ngaged_connect_terms_version(),
        'url' => ngaged_connect_terms_url(),
        'controller' => 'Parvus Media S.L.U.',
        'privacyContact' => 'dpo@parvusmedia.com',
    ];
}

function ngaged_record_terms_acceptance(string $memberId): array
{
    $store = ngaged_members_store();
    $found = ngaged_find_member($store, $memberId);
    if ($found === null) {
        return ['ok' => false, 'error' => 'Invitación no encontrada.'];
    }
    $i = $found['index'];
    $member = $found['member'];
    $ip = trim((string) ($_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? ''));
    if (str_contains($ip, ',')) {
        $ip = trim(explode(',', $ip)[0]);
    }
    $member['termsAcceptance'] = [
        'version' => ngaged_connect_terms_version(),
        'acceptedAt' => gmdate('c'),
        'ipHash' => $ip !== '' ? hash('sha256', $ip . '|' . ngaged_signing_secret()) : null,
    ];
    $store['members'][$i] = $member;
    ngaged_save_members($store);
    return ['ok' => true, 'member' => $member];
}

function ngaged_require_terms_accepted(array $member): ?array
{
    if (ngaged_member_terms_accepted($member)) {
        return null;
    }
    return [
        'ok' => false,
        'error' => 'Debes aceptar las condiciones de Ngaged antes de vincular LinkedIn.',
        'termsRequired' => true,
        'terms' => ngaged_terms_acceptance_meta(),
    ];
}
