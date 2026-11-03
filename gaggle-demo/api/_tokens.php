<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function ngaged_signing_secret(): string
{
    $file = gaggle_demo_load_env();
    $secret = $file['NGAGED_SIGNING_SECRET'] ?? $file['GAGGLE_DEMO_ADMIN_KEY'] ?? gaggle_demo_admin_key();
    return trim($secret);
}

function ngaged_app_base_url(): string
{
    $file = gaggle_demo_load_env();
    $configured = trim($file['NGAGED_APP_URL'] ?? '');
    if ($configured !== '') {
        return rtrim($configured, '/');
    }
    $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    return $scheme . '://' . $host;
}

function ngaged_action_token(string $campaignId, string $memberId, int $ttlSeconds = 604800): string
{
    $payload = [
        'c' => $campaignId,
        'm' => $memberId,
        'e' => time() + $ttlSeconds,
    ];
    $json = json_encode($payload, JSON_UNESCAPED_SLASHES);
    $b64 = rtrim(strtr(base64_encode($json), '+/', '-_'), '=');
    $sig = hash_hmac('sha256', $b64, ngaged_signing_secret());
    return $b64 . '.' . $sig;
}

/** @return array{campaignId:string,memberId:string,exp:int}|null */
function ngaged_verify_action_token(string $token): ?array
{
    $token = trim($token);
    if ($token === '' || !str_contains($token, '.')) {
        return null;
    }
    [$b64, $sig] = explode('.', $token, 2);
    $expected = hash_hmac('sha256', $b64, ngaged_signing_secret());
    if (!hash_equals($expected, $sig)) {
        return null;
    }
    $pad = strlen($b64) % 4;
    if ($pad) {
        $b64 .= str_repeat('=', 4 - $pad);
    }
    $json = base64_decode(strtr($b64, '-_', '+/'), true);
    if ($json === false) {
        return null;
    }
    $data = json_decode($json, true);
    if (!is_array($data) || !isset($data['c'], $data['m'], $data['e'])) {
        return null;
    }
    if ((int) $data['e'] < time()) {
        return null;
    }
    return [
        'campaignId' => (string) $data['c'],
        'memberId' => (string) $data['m'],
        'exp' => (int) $data['e'],
    ];
}

function ngaged_action_url(string $token, string $action): string
{
    return ngaged_app_base_url() . '/go?' . http_build_query([
        'token' => $token,
        'action' => $action,
    ]);
}
