<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_publora.php';

gaggle_demo_cors();

$keyOk = gaggle_demo_api_key() !== '';
$dataDir = gaggle_demo_data_dir();
$writable = is_dir($dataDir) && is_writable($dataDir);

gaggle_demo_json_response(200, [
    'ok' => true,
    'service' => 'ngaged',
    'linkedinPublishReady' => $keyOk,
    'workspaceConnectLinks' => $keyOk && gaggle_publora_workspace_enabled(),
    'dataWritable' => $writable,
]);
