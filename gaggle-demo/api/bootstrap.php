<?php

declare(strict_types=1);

function gaggle_demo_env_paths(): array
{
    return [
        dirname(__DIR__) . '/private/publora.env',
        '/opt/apps/private/gaggle-demo/publora.env',
    ];
}

function gaggle_demo_load_env(): array
{
    static $cache = null;
    if ($cache !== null) {
        return $cache;
    }
    $cache = [];
    foreach (gaggle_demo_env_paths() as $path) {
        if (!is_readable($path)) {
            continue;
        }
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || !str_contains($line, '=')) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $cache[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }
    return $cache;
}

function gaggle_demo_api_key(): string
{
    $file = gaggle_demo_load_env();
    $key = $file['PUBLORA_API_KEY'] ?? getenv('PUBLORA_API_KEY') ?: getenv('publora_api_key') ?: '';
    return trim($key);
}

function gaggle_demo_admin_key(): string
{
    $file = gaggle_demo_load_env();
    $key = $file['GAGGLE_DEMO_ADMIN_KEY'] ?? getenv('GAGGLE_DEMO_ADMIN_KEY') ?: 'demo-admin';
    return trim($key);
}

function gaggle_demo_data_dir(): string
{
    $local = dirname(__DIR__) . '/private/data';
    if (is_dir($local) && is_writable($local)) {
        return $local;
    }
    $vps = '/opt/apps/private/gaggle-demo/data';
    if (is_dir($vps) || @mkdir($vps, 0700, true)) {
        return $vps;
    }
    return $local;
}

function gaggle_demo_json_response(int $code, array $payload): void
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function gaggle_demo_read_json_file(string $name, mixed $default): mixed
{
    $path = gaggle_demo_data_dir() . '/' . $name;
    if (!is_readable($path)) {
        return $default;
    }
    $raw = file_get_contents($path);
    if ($raw === false || trim($raw) === '') {
        return $default;
    }
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : $default;
}

function gaggle_demo_write_json_file(string $name, mixed $data): void
{
    $dir = gaggle_demo_data_dir();
    if (!is_dir($dir)) {
        mkdir($dir, 0700, true);
    }
    $path = $dir . '/' . $name;
    $tmp = $path . '.tmp.' . getmypid();
    file_put_contents($tmp, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    rename($tmp, $path);
}

function gaggle_demo_cors(): void
{
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Demo-Admin-Key');
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(204);
        exit;
    }
}

function gaggle_demo_require_admin(): void
{
    $expected = gaggle_demo_admin_key();
    $got = trim((string) ($_SERVER['HTTP_X_DEMO_ADMIN_KEY'] ?? ''));
    if ($got === '' || !hash_equals($expected, $got)) {
        gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Admin key required.']);
    }
}

function gaggle_demo_new_id(string $prefix): string
{
    return $prefix . '_' . bin2hex(random_bytes(8));
}
