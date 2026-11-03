<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';

gaggle_demo_cors();
ngaged_maybe_migrate_legacy();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

$platformId = trim((string) ($_GET['platformId'] ?? ''));
if ($platformId === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'platformId required']);
}

$membersStore = ngaged_members_store();
$memberIds = [];
foreach ($membersStore['members'] ?? [] as $m) {
    if (is_array($m) && ($m['platformId'] ?? '') === $platformId) {
        $memberIds[] = (string) ($m['id'] ?? '');
    }
}

$pending = [];
foreach (ngaged_campaigns_store()['campaigns'] ?? [] as $c) {
    if (!is_array($c) || empty($c['dispatchedAt'])) {
        continue;
    }
    foreach ($c['deliveries'] ?? [] as $d) {
        if (!is_array($d) || !empty($d['respondedAt'])) {
            continue;
        }
        $mid = (string) ($d['memberId'] ?? '');
        if ($memberIds !== [] && !in_array($mid, $memberIds, true)) {
            continue;
        }
        if (($d['platformId'] ?? '') === $platformId || in_array($mid, $memberIds, true)) {
            $pending[] = [
                'campaignId' => $c['id'],
                'title' => $c['title'],
                'commentary' => $c['commentary'] ?? '',
                'preview' => $c['preview'] ?? [],
                'memberId' => $mid,
                'sentAt' => $d['sentAt'] ?? null,
            ];
        }
    }
}

gaggle_demo_json_response(200, ['ok' => true, 'pending' => $pending]);
