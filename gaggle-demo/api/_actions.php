<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_publora.php';

/**
 * @return array{ok:bool,error?:string,delivery?:array,campaign?:array}
 */
function ngaged_apply_campaign_action(string $campaignId, string $memberId, string $action): array
{
    if (!in_array($action, ['approve', 'decline'], true)) {
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

    $members = ngaged_members_store();
    $memberRow = ngaged_find_member($members, $memberId);
    $platformId = trim((string) ($delivery['platformId'] ?? ''));
    if ($platformId === '' && $memberRow !== null) {
        $platformId = trim((string) ($memberRow['member']['platformId'] ?? ''));
    }

    $delivery['respondedAt'] = gmdate('c');
    $delivery['action'] = $action;

    if ($action === 'approve') {
        if ($platformId === '') {
            $delivery['error'] = 'Cuenta LinkedIn no configurada.';
            $deliveries[$dIdx] = $delivery;
            $campaign['deliveries'] = $deliveries;
            $store['campaigns'][$idx] = $campaign;
            ngaged_save_campaigns($store);
            return ['ok' => false, 'error' => 'No pudimos republicar: falta la cuenta LinkedIn.'];
        }

        $urn = trim((string) ($campaign['repostParentUrn'] ?? ''));
        $commentary = trim((string) ($campaign['commentary'] ?? ''));
        $pub = gaggle_publora_linkedin_reshare($platformId, $urn, $commentary);
        if (!$pub['ok']) {
            $delivery['error'] = (string) ($pub['error'] ?? 'Error al republicar.');
            $deliveries[$dIdx] = $delivery;
            $campaign['deliveries'] = $deliveries;
            $store['campaigns'][$idx] = $campaign;
            ngaged_save_campaigns($store);
            return ['ok' => false, 'error' => 'No pudimos republicar en LinkedIn. ' . ($pub['error'] ?? '')];
        }
        $delivery['postGroupId'] = $pub['postGroupId'] ?? null;
        $delivery['error'] = null;
    }

    $deliveries[$dIdx] = $delivery;
    $campaign['deliveries'] = $deliveries;
    $store['campaigns'][$idx] = $campaign;
    ngaged_save_campaigns($store);

    return ['ok' => true, 'delivery' => $delivery, 'campaign' => $campaign];
}
