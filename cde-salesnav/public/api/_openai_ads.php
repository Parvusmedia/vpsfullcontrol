<?php
/**
 * OpenAI Ads — Measurement Pixel (browser) + Conversions API (server).
 * @see https://developers.openai.com/ads/conversion-tracking
 */

declare(strict_types=1);

function cde_openai_ads_env_paths(): array
{
    return [
        dirname(__DIR__, 2) . '/private/cde/stripe.env',
        '/var/www/vhosts/companydataenrichment.com/private/cde/stripe.env',
        '/opt/apps/private/cde/stripe.env',
    ];
}

/** @return array<string, string> */
function cde_openai_ads_read_env(): array
{
    static $cache = null;
    if (is_array($cache)) {
        return $cache;
    }
    $cache = [];
    foreach (cde_openai_ads_env_paths() as $path) {
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

function cde_openai_ads_pixel_id(): string
{
    $env = cde_openai_ads_read_env();
    return trim($env['OPENAI_ADS_PIXEL_ID'] ?? getenv('OPENAI_ADS_PIXEL_ID') ?: 'NQH4BHyBvLncEkDLpUrQpJ');
}

function cde_openai_ads_conversions_api_key(): string
{
    $env = cde_openai_ads_read_env();
    return trim($env['OPENAI_CONVERSIONS_API_KEY'] ?? getenv('OPENAI_CONVERSIONS_API_KEY') ?: '');
}

function cde_openai_ads_dedupe_store(): string
{
    $dir = dirname(__DIR__, 2) . '/private/cde';
    if (!is_dir($dir)) {
        $dir = '/var/www/vhosts/companydataenrichment.com/private/cde';
    }
    return $dir . '/openai_ads_sent.json';
}

function cde_openai_ads_already_sent(string $eventId): bool
{
    $eventId = trim($eventId);
    if ($eventId === '') {
        return true;
    }
    $path = cde_openai_ads_dedupe_store();
    if (!is_readable($path)) {
        return false;
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) && !empty($data[$eventId]);
}

function cde_openai_ads_mark_sent(string $eventId): void
{
    $eventId = trim($eventId);
    if ($eventId === '') {
        return;
    }
    $path = cde_openai_ads_dedupe_store();
    $data = [];
    if (is_readable($path)) {
        $decoded = json_decode((string) file_get_contents($path), true);
        if (is_array($decoded)) {
            $data = $decoded;
        }
    }
    $data[$eventId] = gmdate('c');
    // Keep store bounded.
    if (count($data) > 5000) {
        $data = array_slice($data, -4000, null, true);
    }
    $dir = dirname($path);
    if (!is_dir($dir)) {
        @mkdir($dir, 0700, true);
    }
    @file_put_contents($path, json_encode($data, JSON_UNESCAPED_SLASHES), LOCK_EX);
}

function cde_openai_ads_landing_source_url(): string
{
    return 'https://companydataenrichment.com/salesnav/';
}

/**
 * @param list<array<string, mixed>> $events
 */
function cde_openai_ads_post_events(array $events, bool $validateOnly = false): bool
{
    $pixelId = cde_openai_ads_pixel_id();
    $apiKey = cde_openai_ads_conversions_api_key();
    if ($pixelId === '' || $apiKey === '' || $events === []) {
        return false;
    }

    $payload = [
        'validate_only' => $validateOnly,
        'events' => $events,
    ];

    $url = 'https://bzr.openai.com/v1/events?pid=' . rawurlencode($pixelId);
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'Authorization: Bearer ' . $apiKey,
            'Content-Type: application/json',
        ],
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        CURLOPT_TIMEOUT => 15,
    ]);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return $raw !== false && $code >= 200 && $code < 300;
}

/**
 * Landing arrival (ad campaigns). Idempotent per event id.
 */
function cde_openai_ads_track_contents_viewed(
    string $eventId,
    string $sourceUrl = ''
): bool {
    $eventId = trim($eventId);
    if ($eventId === '' || cde_openai_ads_already_sent($eventId)) {
        return false;
    }
    if ($sourceUrl === '') {
        $sourceUrl = cde_openai_ads_landing_source_url();
    }

    $ok = cde_openai_ads_post_events([
        [
            'id' => $eventId,
            'type' => 'contents_viewed',
            'timestamp_ms' => (int) round(microtime(true) * 1000),
            'source_url' => $sourceUrl,
            'action_source' => 'web',
            'data' => [
                'type' => 'contents',
            ],
        ],
    ]);

    if ($ok) {
        cde_openai_ads_mark_sent($eventId);
    }

    return $ok;
}

/**
 * Server-side order_created (top-up). Idempotent per event id (Stripe session id).
 */
function cde_openai_ads_track_order_created(
    string $eventId,
    int $amountCents,
    string $currency = 'EUR',
    string $sourceUrl = 'https://companydataenrichment.com/salesnav/panel/#topup'
): bool {
    $eventId = trim($eventId);
    if ($eventId === '' || cde_openai_ads_already_sent($eventId)) {
        return false;
    }

    $ok = cde_openai_ads_post_events([
        [
            'id' => $eventId,
            'type' => 'order_created',
            'timestamp_ms' => (int) round(microtime(true) * 1000),
            'source_url' => $sourceUrl,
            'action_source' => 'web',
            'data' => [
                'type' => 'contents',
                'amount' => max(0, $amountCents),
                'currency' => strtoupper($currency !== '' ? $currency : 'EUR'),
            ],
        ],
    ]);

    if ($ok) {
        cde_openai_ads_mark_sent($eventId);
    }

    return $ok;
}

/** @param array<string, mixed> $session Stripe checkout.session */
function cde_openai_ads_track_checkout_session(array $session): void
{
    $sessionId = (string) ($session['id'] ?? '');
    if ($sessionId === '') {
        return;
    }
    $amount = (int) ($session['amount_total'] ?? 0);
    $currency = (string) ($session['currency'] ?? 'eur');
    cde_openai_ads_track_order_created($sessionId, $amount, $currency);
}
