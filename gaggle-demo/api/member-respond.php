<?php

declare(strict_types=1);

require_once __DIR__ . '/_actions.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$campaignId = trim((string) ($input['campaignId'] ?? ''));
$memberId = trim((string) ($input['memberId'] ?? ''));
$platformId = trim((string) ($input['platformId'] ?? ''));
$action = trim((string) ($input['action'] ?? ''));

if ($campaignId === '' || $memberId === '' || $action === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Parámetros incompletos.']);
}

if ($platformId !== '') {
    $store = ngaged_campaigns_store();
    $found = ngaged_find_campaign($store, $campaignId);
    if ($found !== null) {
        $idx = $found['index'];
        $campaign = $found['campaign'];
        foreach ($campaign['deliveries'] ?? [] as $i => $d) {
            if (is_array($d) && ($d['memberId'] ?? '') === $memberId) {
                $campaign['deliveries'][$i]['platformId'] = $platformId;
                $store['campaigns'][$idx] = $campaign;
                ngaged_save_campaigns($store);
                break;
            }
        }
    }
}

$result = ngaged_apply_campaign_action($campaignId, $memberId, $action);
if (!$result['ok']) {
    gaggle_demo_json_response(422, ['ok' => false, 'error' => $result['error'] ?? 'Error']);
}

gaggle_demo_json_response(200, ['ok' => true, 'delivery' => $result['delivery'] ?? null]);
