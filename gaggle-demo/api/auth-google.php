<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';

ngaged_session_start();
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$isCallback = str_ends_with($path, '/callback');

$env = gaggle_demo_load_env();
$clientId = trim($env['GOOGLE_CLIENT_ID'] ?? '');
$clientSecret = trim($env['GOOGLE_CLIENT_SECRET'] ?? '');
$appUrl = ngaged_app_url();

if ($clientId === '' || $clientSecret === '') {
    if ($isCallback) {
        header('Location: ' . $appUrl . '/login?error=google_not_configured');
        exit;
    }
    gaggle_demo_json_response(503, ['ok' => false, 'error' => 'Google Sign-In no está configurado en el servidor.']);
}

$redirectUri = $appUrl . '/api/auth-google/callback';

if (!$isCallback) {
    $state = bin2hex(random_bytes(16));
    $_SESSION['google_oauth_state'] = $state;
    $params = http_build_query([
        'client_id' => $clientId,
        'redirect_uri' => $redirectUri,
        'response_type' => 'code',
        'scope' => 'openid email profile',
        'state' => $state,
        'prompt' => 'select_account',
    ]);
    header('Location: https://accounts.google.com/o/oauth2/v2/auth?' . $params);
    exit;
}

// Callback
$code = (string) ($_GET['code'] ?? '');
$state = (string) ($_GET['state'] ?? '');
if ($code === '' || $state === '' || !hash_equals((string) ($_SESSION['google_oauth_state'] ?? ''), $state)) {
    header('Location: ' . $appUrl . '/login?error=google_denied');
    exit;
}
unset($_SESSION['google_oauth_state']);

$tokenRes = ngaged_google_token_exchange($code, $clientId, $clientSecret, $redirectUri);
if (!$tokenRes['ok']) {
    header('Location: ' . $appUrl . '/login?error=google_token');
    exit;
}
$idToken = $tokenRes['id_token'] ?? '';
$claims = ngaged_google_verify_id_token($idToken, $clientId);
if ($claims === null) {
    header('Location: ' . $appUrl . '/login?error=google_verify');
    exit;
}

$email = strtolower(trim((string) ($claims['email'] ?? '')));
if ($email === '' || empty($claims['email_verified'])) {
    header('Location: ' . $appUrl . '/login?error=google_email');
    exit;
}

ngaged_bootstrap_admin_from_env();
$store = ngaged_admins_store();
$found = ngaged_find_admin_by_email($store, $email);
if ($found === null) {
    header('Location: ' . $appUrl . '/login?error=no_access');
    exit;
}

$admin = $found['admin'];
session_regenerate_id(true);
$_SESSION['ngaged_admin_id'] = $admin['id'];
$_SESSION['ngaged_admin_email'] = $admin['email'];
header('Location: ' . $appUrl . '/');
exit;

/** @return array{ok:bool,id_token?:string,error?:string} */
function ngaged_google_token_exchange(string $code, string $clientId, string $clientSecret, string $redirectUri): array
{
    $body = http_build_query([
        'code' => $code,
        'client_id' => $clientId,
        'client_secret' => $clientSecret,
        'redirect_uri' => $redirectUri,
        'grant_type' => 'authorization_code',
    ]);
    $ctx = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => $body,
            'timeout' => 20,
        ],
    ]);
    $raw = @file_get_contents('https://oauth2.googleapis.com/token', false, $ctx);
    if ($raw === false) {
        return ['ok' => false, 'error' => 'token_request_failed'];
    }
    $data = json_decode($raw, true);
    if (!is_array($data) || empty($data['id_token'])) {
        return ['ok' => false, 'error' => 'token_invalid'];
    }
    return ['ok' => true, 'id_token' => (string) $data['id_token']];
}

/** @return array<string,mixed>|null */
function ngaged_google_verify_id_token(string $idToken, string $clientId): ?array
{
    $url = 'https://oauth2.googleapis.com/tokeninfo?id_token=' . rawurlencode($idToken);
    $raw = @file_get_contents($url);
    if ($raw === false) {
        return null;
    }
    $data = json_decode($raw, true);
    if (!is_array($data)) {
        return null;
    }
    if (($data['aud'] ?? '') !== $clientId) {
        return null;
    }
    if ((int) ($data['exp'] ?? 0) < time()) {
        return null;
    }
    return $data;
}
