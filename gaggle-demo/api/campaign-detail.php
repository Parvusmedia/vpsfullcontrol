<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

gaggle_demo_require_admin();
$id = trim((string) ($_GET['id'] ?? ''));
if ($id === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'id required']);
}

$store = ngaged_campaigns_store();
$found = ngaged_find_campaign($store, $id);
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Not found']);
}

$membersStore = ngaged_members_store();
$names = [];
foreach ($membersStore['members'] ?? [] as $m) {
    if (is_array($m)) {
        $names[(string) ($m['id'] ?? '')] = (string) ($m['name'] ?? $m['email'] ?? '');
    }
}

$campaign = $found['campaign'];
$rows = [];
foreach ($campaign['deliveries'] ?? [] as $d) {
    if (!is_array($d)) {
        continue;
    }
    $mid = (string) ($d['memberId'] ?? '');
    $rows[] = [
        'memberId' => $mid,
        'name' => $names[$mid] ?? $d['email'] ?? '—',
        'email' => $d['email'] ?? '',
        'sentAt' => $d['sentAt'] ?? null,
        'respondedAt' => $d['respondedAt'] ?? null,
        'action' => $d['action'] ?? null,
        'error' => $d['error'] ?? null,
    ];
}

gaggle_demo_json_response(200, ['ok' => true, 'campaign' => $campaign, 'deliveries' => $rows]);
