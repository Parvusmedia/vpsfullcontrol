<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_publora.php';
require_once __DIR__ . '/_mail.php';

gaggle_demo_cors();

$keyOk = gaggle_demo_api_key() !== '';
$dataDir = gaggle_demo_data_dir();
$writable = is_dir($dataDir) && is_writable($dataDir);

$oauth = $keyOk && gaggle_publora_workspace_enabled();
$adminKey = gaggle_demo_admin_key();
$defaultAdmin = $adminKey === '' || $adminKey === 'demo-admin';

gaggle_demo_json_response(200, [
    'ok' => true,
    'service' => 'ngaged',
    'linkedinPublishReady' => $keyOk,
    'workspaceConnectLinks' => $oauth,
    'linkedinOAuth' => $oauth,
    'dataWritable' => $writable,
    'mailFromConfigured' => ngaged_mail_from() !== '',
    'mailTransport' => function_exists('mail') ? 'php-mail' : 'unavailable',
    'adminKeyConfigured' => !$defaultAdmin,
    'checks' => [
        ['id' => 'api', 'label' => 'API de publicación LinkedIn', 'ok' => $keyOk],
        ['id' => 'oauth', 'label' => 'OAuth LinkedIn por empleado', 'ok' => $oauth],
        ['id' => 'data', 'label' => 'Almacenamiento de datos', 'ok' => $writable],
        ['id' => 'mail', 'label' => 'Envío de email (SMTP/php-mail)', 'ok' => function_exists('mail')],
        ['id' => 'admin', 'label' => 'Clave admin personalizada', 'ok' => !$defaultAdmin],
    ],
]);
