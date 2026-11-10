<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_publora.php';

/** Delay entre like y repost (segundos) para parecer más natural en LinkedIn. */
function ngaged_like_repost_delay_seconds(): int
{
    return random_int(10, 20);
}

/** @return list<string> */
function ngaged_valid_member_actions(): array
{
    return ['like', 'repost', 'like_repost', 'decline', 'approve'];
}

function ngaged_normalize_member_action(string $action): ?string
{
    $action = strtolower(trim($action));
    if ($action === 'approve') {
        return 'repost';
    }
    if (!in_array($action, ['like', 'repost', 'like_repost', 'decline'], true)) {
        return null;
    }
    return $action;
}

function ngaged_action_includes_repost(string $normalizedAction): bool
{
    return in_array($normalizedAction, ['repost', 'like_repost'], true);
}

function ngaged_action_includes_like(string $normalizedAction): bool
{
    return in_array($normalizedAction, ['like', 'like_repost'], true);
}

/**
 * @return array{ok:bool,error?:string,delivery?:array,campaign?:array}
 */
function ngaged_apply_campaign_action(string $campaignId, string $memberId, string $action): array
{
    $action = ngaged_normalize_member_action($action);
    if ($action === null) {
        return ['ok' => false, 'error' => 'Acción no válida.'];
    }

    $store = ngaged_campaigns_store();
    $found = ngaged_find_campaign($store, $campaignId);
    if ($found === null) {
        return ['ok' => false, 'error' => 'Campaña no encontrada.'];
    }

    $idx = $found['index'];
    $campaign = $found['campaign'];
    $deliveries = $campaign['deliveries'] ?? [];
    if (!is_array($deliveries)) {
        $deliveries = [];
    }

    $dIdx = null;
    foreach ($deliveries as $i => $d) {
        if (is_array($d) && ($d['memberId'] ?? '') === $memberId) {
            $dIdx = $i;
            break;
        }
    }

    if ($dIdx === null) {
        return ['ok' => false, 'error' => 'No estás en la audiencia de esta campaña.'];
    }

    $delivery = $deliveries[$dIdx];
    if (!empty($delivery['respondedAt'])) {
        return ['ok' => false, 'error' => 'Ya respondiste a esta campaña.'];
    }

    if ($action === 'decline') {
        $delivery['respondedAt'] = gmdate('c');
        $delivery['action'] = 'decline';
        $deliveries[$dIdx] = $delivery;
        $campaign['deliveries'] = $deliveries;
        $store['campaigns'][$idx] = $campaign;
        ngaged_save_campaigns($store);
        return ['ok' => true, 'delivery' => $delivery, 'campaign' => $campaign];
    }

    $members = ngaged_members_store();
    $memberRow = ngaged_find_member($members, $memberId);
    $platformId = trim((string) ($delivery['platformId'] ?? ''));
    if ($platformId === '' && $memberRow !== null) {
        $platformId = trim((string) ($memberRow['member']['platformId'] ?? ''));
    }

    if ($platformId === '') {
        return ['ok' => false, 'error' => 'No pudimos actuar: falta la cuenta LinkedIn vinculada.'];
    }

    $urn = trim((string) ($campaign['repostParentUrn'] ?? ''));
    if ($urn === '') {
        return ['ok' => false, 'error' => 'Campaña sin URN de post LinkedIn.'];
    }

    $commentary = trim((string) ($campaign['commentary'] ?? ''));

    if (ngaged_action_includes_like($action)) {
        $like = gaggle_publora_linkedin_like($platformId, $urn, 'LIKE');
        if (!$like['ok']) {
            $delivery['error'] = (string) ($like['error'] ?? 'Error al dar me gusta.');
            $deliveries[$dIdx] = $delivery;
            $campaign['deliveries'] = $deliveries;
            $store['campaigns'][$idx] = $campaign;
            ngaged_save_campaigns($store);
            return ['ok' => false, 'error' => 'No pudimos dar me gusta en LinkedIn. ' . ($like['error'] ?? '')];
        }
        $delivery['likedAt'] = gmdate('c');
        $delivery['reactionType'] = 'LIKE';
    }

    if ($action === 'like_repost') {
        $delay = ngaged_like_repost_delay_seconds();
        $delivery['repostDelaySeconds'] = $delay;
        sleep($delay);
    }

    if (ngaged_action_includes_repost($action)) {
        $pub = gaggle_publora_linkedin_reshare($platformId, $urn, $commentary);
        if (!$pub['ok']) {
            $delivery['respondedAt'] = gmdate('c');
            $delivery['action'] = $action;
            $delivery['error'] = (string) ($pub['error'] ?? 'Error al republicar.');
            $deliveries[$dIdx] = $delivery;
            $campaign['deliveries'] = $deliveries;
            $store['campaigns'][$idx] = $campaign;
            ngaged_save_campaigns($store);
            $hint = $action === 'like_repost'
                ? 'El me gusta sí se registró, pero el repost falló.'
                : 'No pudimos republicar en LinkedIn.';
            return ['ok' => false, 'error' => $hint . ' ' . ($pub['error'] ?? '')];
        }
        $delivery['postGroupId'] = $pub['postGroupId'] ?? null;
        $delivery['repostedAt'] = gmdate('c');
        $delivery['error'] = null;
    }

    $delivery['respondedAt'] = gmdate('c');
    $delivery['action'] = $action;
    $deliveries[$dIdx] = $delivery;
    $campaign['deliveries'] = $deliveries;
    $store['campaigns'][$idx] = $campaign;
    ngaged_save_campaigns($store);

    return ['ok' => true, 'delivery' => $delivery, 'campaign' => $campaign];
}

function ngaged_action_success_message(string $action): string
{
    return match ($action) {
        'like' => '¡Gracias! Hemos dado me gusta al post en LinkedIn.',
        'repost' => '¡Gracias! Tu repost se ha publicado en LinkedIn.',
        'like_repost' => '¡Listo! Me gusta y repost publicados en LinkedIn.',
        'decline' => 'Entendido. Has ignorado esta campaña.',
        default => 'Acción registrada.',
    };
}
