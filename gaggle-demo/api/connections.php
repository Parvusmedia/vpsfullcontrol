<?php

declare(strict_types=1);

require_once __DIR__ . '/_publora.php';
require_once __DIR__ . '/_publora_company.php';

gaggle_demo_cors();

require_once __DIR__ . '/bootstrap.php';
gaggle_demo_require_admin();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

$result = gaggle_publora_list_connections();
if (!$result['ok']) {
    gaggle_demo_json_response(502, [
        'ok' => false,
        'error' => ngaged_user_error_message(
            $result['error'] ?? null,
            'No pudimos cargar las cuentas LinkedIn. Inténtalo más tarde.'
        ),
    ]);
}

$connections = [];
if (gaggle_publora_company_configured()) {
    foreach (gaggle_publora_company_list_channels() as $row) {
        $connections[] = [
            'platformId' => $row['platformId'],
            'username' => $row['username'],
            'profileUrl' => null,
            'profileImageUrl' => null,
            'tokenStatus' => null,
            'connectionStatus' => $row['status'],
            'source' => 'workspace',
        ];
    }
}

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
        'source' => 'account',
    ];
}

$seen = [];
$deduped = [];
foreach ($connections as $c) {
    $pid = (string) ($c['platformId'] ?? '');
    if ($pid === '' || isset($seen[$pid])) {
        continue;
    }
    $seen[$pid] = true;
    $deduped[] = $c;
}
$connections = $deduped;

gaggle_demo_json_response(200, ['ok' => true, 'connections' => $connections]);
