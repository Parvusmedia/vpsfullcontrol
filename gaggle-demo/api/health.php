<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_publora.php';
require_once __DIR__ . '/_mail.php';
require_once __DIR__ . '/_admin_auth.php';
require_once __DIR__ . '/_admin_2fa.php';

gaggle_demo_cors();

$keyOk = gaggle_demo_api_key() !== '';
$dataDir = gaggle_demo_data_dir();
$writable = is_dir($dataDir) && is_writable($dataDir);

$oauth = $keyOk && gaggle_publora_workspace_enabled();
ngaged_bootstrap_admin_from_env();
$adminStore = ngaged_admins_store();
$hasAdmins = count($adminStore['admins'] ?? []) > 0;
$adminKey = gaggle_demo_admin_key();
$legacyKeySet = $adminKey !== '' && $adminKey !== 'demo-admin';

gaggle_demo_json_response(200, [
    'ok' => true,
    'service' => 'ngaged',
    'linkedinPublishReady' => $keyOk,
    'workspaceConnectLinks' => $oauth,
    'linkedinOAuth' => $oauth,
    'dataWritable' => $writable,
    'mailFromConfigured' => ngaged_mail_from() !== '',
    'mailTransport' => function_exists('mail') ? 'php-mail' : 'unavailable',
    'adminUsersConfigured' => $hasAdmins,
    'googleLoginConfigured' => ngaged_google_oauth_configured(),
    'checks' => [
        ['id' => 'api', 'label' => 'API de publicación LinkedIn', 'ok' => $keyOk],
        ['id' => 'oauth', 'label' => 'OAuth LinkedIn por empleado', 'ok' => $oauth],
        ['id' => 'data', 'label' => 'Almacenamiento de datos', 'ok' => $writable],
        ['id' => 'mail', 'label' => 'Envío de email (SMTP/php-mail)', 'ok' => function_exists('mail')],
        ['id' => 'admin', 'label' => 'Cuentas de administrador', 'ok' => $hasAdmins],
        ['id' => 'google', 'label' => 'Login con Google (opcional)', 'ok' => ngaged_google_oauth_configured()],
        ['id' => '2fa', 'label' => '2FA admin por email', 'ok' => !ngaged_admin_2fa_enabled() || function_exists('mail')],
    ],
]);
