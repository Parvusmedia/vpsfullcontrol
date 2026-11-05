<?php

declare(strict_types=1);

require_once __DIR__ . '/_publora.php';

gaggle_demo_cors();

require_once __DIR__ . '/bootstrap.php';
gaggle_demo_require_admin();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

$result = gaggle_publora_list_connections();
if (!$result['ok']) {
    gaggle_demo_json_response(502, ['ok' => false, 'error' => $result['error'] ?? 'Publora error']);
}

$connections = [];
foreach ($result['connections'] as $row) {
    if (!is_array($row)) {
        continue;
    }
    $platformId = (string) ($row['platformId'] ?? $row['id'] ?? '');
    if ($platformId === '') {
        continue;
    }
    $connections[] = [
        'platformId' => $platformId,
        'username' => $row['username'] ?? $row['displayName'] ?? null,
        'profileUrl' => $row['profileUrl'] ?? null,
        'profileImageUrl' => $row['profileImageUrl'] ?? null,
        'tokenStatus' => $row['tokenStatus'] ?? null,
        'connectionStatus' => $row['connectionStatus'] ?? null,
    ];
}

gaggle_demo_json_response(200, ['ok' => true, 'connections' => $connections]);
