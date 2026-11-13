<?php

declare(strict_types=1);

require dirname(__DIR__) . '/api/bootstrap.php';

$key = gaggle_demo_api_key();
$ws = getenv('PUBLORA_WORKSPACE_ID') ?: 'a397359092b779cd23e055b0';
$companyId = getenv('PUBLORA_EXTERNAL_COMPANY_ID') ?: '19912f4b005051fa22b806e0';
$cred = $argv[1] ?? '00000000-0000-4000-8000-ngagedtest01';

$body = json_encode([
    'platform' => 'linkedin',
    'connectionSubtype' => 'personal',
    'externalOwner' => [
        'instanceId' => 'ngaged',
        'companyId' => strtolower($companyId),
        'credentialId' => strtolower($cred),
    ],
], JSON_UNESCAPED_SLASHES);

$ch = curl_init('https://api.publora.com/api/v1/company/connection-link');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $body,
    CURLOPT_HTTPHEADER => [
        'x-publora-key: ' . $key,
        'x-publora-client: ngaged',
        'X-Publora-Workspace-Id: ' . $ws,
        'Content-Type: application/json',
        'Accept: application/json',
    ],
]);
$raw = curl_exec($ch);
$http = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

fwrite(STDERR, "http={$http}\n");
echo $raw . "\n";
