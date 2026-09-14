<?php
/**
 * OpenAI Ads Conversion API proxy — keeps the API key off the browser.
 */
declare(strict_types=1);

require_once __DIR__ . '/lib/env.php';

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

function oai_json(int $code, array $payload): void
{
    http_response_code($code);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

function oai_origin_ok(): bool
{
    $allowed = 'https://parvusmedia.com';
    $origin = rtrim((string)($_SERVER['HTTP_ORIGIN'] ?? ''), '/');
    if ($origin !== '') {
        return $origin === $allowed || $origin === 'https://www.parvusmedia.com';
    }
    $referer = (string)($_SERVER['HTTP_REFERER'] ?? '');
    if ($referer === '') {
        $ip = (string)($_SERVER['REMOTE_ADDR'] ?? '');
        return $ip === '127.0.0.1' || $ip === '::1';
    }
    return strpos($referer, 'https://parvusmedia.com/') === 0
        || strpos($referer, 'https://www.parvusmedia.com/') === 0;
}

function oai_rate_ok(string $ip): bool
{
    $file = sys_get_temp_dir() . '/parvus_oai_' . hash('sha256', $ip);
    $now = time();
    $hits = [];
    if (is_readable($file)) {
        $raw = file_get_contents($file);
        $hits = $raw ? array_filter(array_map('intval', explode("\n", $raw))) : [];
    }
    $hits = array_values(array_filter($hits, function ($t) use ($now) {
        return ($now - $t) < 60;
    }));
    if (count($hits) >= 20) {
        return false;
    }
    $hits[] = $now;
    @file_put_contents($file, implode("\n", $hits), LOCK_EX);
    return true;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    oai_json(405, ['ok' => false, 'error' => 'Method not allowed']);
}

if (!oai_origin_ok()) {
    oai_json(403, ['ok' => false, 'error' => 'Forbidden']);
}

$ip = (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
if (!oai_rate_ok($ip)) {
    oai_json(429, ['ok' => false, 'error' => 'Rate limited']);
}

$raw = file_get_contents('php://input');
$in = is_string($raw) ? json_decode($raw, true) : null;
if (!is_array($in)) {
    oai_json(400, ['ok' => false, 'error' => 'Invalid JSON']);
}

$type = trim((string)($in['type'] ?? ''));
$allowed = [
    'contents_viewed' => 'contents',
    'appointment_scheduled' => 'customer_action',
];
if (!isset($allowed[$type])) {
    oai_json(400, ['ok' => false, 'error' => 'Unknown event']);
}

$sourceUrl = trim((string)($in['source_url'] ?? ''));
if ($sourceUrl === '' || !filter_var($sourceUrl, FILTER_VALIDATE_URL)) {
    oai_json(400, ['ok' => false, 'error' => 'Invalid source_url']);
}
$host = parse_url($sourceUrl, PHP_URL_HOST);
if (!is_string($host) || !in_array(strtolower($host), ['parvusmedia.com', 'www.parvusmedia.com'], true)) {
    oai_json(400, ['ok' => false, 'error' => 'Invalid source_url']);
}

$eventId = preg_replace('/[^a-zA-Z0-9._-]/', '', (string)($in['id'] ?? ''));
if ($eventId === '') {
    $eventId = bin2hex(random_bytes(16));
}
if (strlen($eventId) > 80) {
    $eventId = substr($eventId, 0, 80);
}

$env = parvus_web_read_env('openai-ads.env');
$pixelId = trim((string)($env['OPENAI_ADS_PIXEL_ID'] ?? 'SBNmyZzRGpsz8rh413aMQN'));
$apiKey = trim((string)($env['OPENAI_ADS_CAPI_KEY'] ?? ''));
if ($apiKey === '') {
    oai_json(503, ['ok' => false, 'error' => 'Not configured']);
}

$payload = [
    'validate_only' => false,
    'events' => [[
        'id' => $eventId,
        'type' => $type,
        'timestamp_ms' => (int)round(microtime(true) * 1000),
        'source_url' => $sourceUrl,
        'action_source' => 'web',
        'data' => [
            'type' => $allowed[$type],
        ],
    ]],
];

$ch = curl_init('https://bzr.openai.com/v1/events?pid=' . rawurlencode($pixelId));
if ($ch === false) {
    oai_json(502, ['ok' => false, 'error' => 'Upstream init failed']);
}
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $apiKey,
        'Content-Type: application/json',
    ],
    CURLOPT_POSTFIELDS => json_encode($payload),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 8,
]);
$response = curl_exec($ch);
$status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($response === false || $status < 200 || $status >= 300) {
    oai_json(502, ['ok' => false, 'error' => 'Upstream failed']);
}

oai_json(200, ['ok' => true]);
