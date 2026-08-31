<?php
/**
 * Stripe Checkout for NavExport prepaid credits.
 */

declare(strict_types=1);

require_once __DIR__ . '/_credits.php';

function cde_stripe_config(): array
{
    $env = cde_credits_read_env();
    $secret = $env['STRIPE_SECRET_KEY'] ?? getenv('STRIPE_SECRET_KEY') ?: '';
    $webhook = $env['STRIPE_WEBHOOK_SECRET'] ?? getenv('STRIPE_WEBHOOK_SECRET') ?: '';
    $origin = $env['SALESNAV_SITE_ORIGIN'] ?? getenv('SALESNAV_SITE_ORIGIN') ?: 'https://companydataenrichment.com';

    if ($secret === '') {
        cde_json_response(503, [
            'ok' => false,
            'error' => 'Billing is not configured yet.',
        ]);
    }

    return [
        'secret_key' => $secret,
        'webhook_secret' => $webhook,
        'origin' => rtrim($origin, '/'),
    ];
}

function cde_stripe_request(string $method, string $path, array $fields): array
{
    $cfg = cde_stripe_config();
    $body = http_build_query($fields);
    $ch = curl_init('https://api.stripe.com/v1/' . ltrim($path, '/'));
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => strtoupper($method),
        CURLOPT_HTTPHEADER => [
            'Authorization: Bearer ' . $cfg['secret_key'],
            'Content-Type: application/x-www-form-urlencoded',
        ],
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_TIMEOUT => 30,
    ]);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    $data = json_decode((string) $raw, true);
    if (!is_array($data)) {
        $data = [];
    }
    if ($code >= 400) {
        $msg = $data['error']['message'] ?? 'Stripe API error';
        return ['ok' => false, 'status' => $code, 'error' => (string) $msg];
    }
    return ['ok' => true, 'status' => $code, 'data' => $data];
}

function cde_stripe_create_checkout_session(string $userId, string $packId): array
{
    $packs = cde_credits_packs();
    if (!isset($packs[$packId])) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid credit pack.']);
    }
    $pack = $packs[$packId];
    $cfg = cde_stripe_config();

    $fields = [
        'mode' => 'payment',
        'success_url' => $cfg['origin'] . '/salesnav/?credits=1',
        'cancel_url' => $cfg['origin'] . '/salesnav/?credits=0',
        'client_reference_id' => $userId,
        'metadata[user_id]' => $userId,
        'metadata[pack_id]' => $packId,
        'metadata[credits]' => (string) $pack['credits'],
        'line_items[0][quantity]' => '1',
        'line_items[0][price_data][currency]' => 'eur',
        'line_items[0][price_data][unit_amount]' => (string) $pack['amount_cents'],
        'line_items[0][price_data][product_data][name]' => $pack['label'],
        'line_items[0][price_data][product_data][description]' => 'NavExport — 1 credit = 1 exported lead (Basic tier)',
    ];

    $resp = cde_stripe_request('POST', 'checkout/sessions', $fields);
    if (!$resp['ok']) {
        cde_json_response($resp['status'] >= 400 ? $resp['status'] : 502, [
            'ok' => false,
            'error' => $resp['error'] ?? 'Could not start Stripe checkout.',
        ]);
    }

    $url = (string) ($resp['data']['url'] ?? '');
    if ($url === '') {
        cde_json_response(502, ['ok' => false, 'error' => 'Stripe did not return a checkout URL.']);
    }

    return [
        'url' => $url,
        'session_id' => (string) ($resp['data']['id'] ?? ''),
        'credits' => $pack['credits'],
        'amount_cents' => $pack['amount_cents'],
    ];
}

function cde_stripe_verify_webhook(string $payload, string $sigHeader): array
{
    $cfg = cde_stripe_config();
    $secret = $cfg['webhook_secret'];
    if ($secret === '') {
        return ['ok' => false, 'error' => 'Webhook secret not configured'];
    }

    $parts = [];
    foreach (explode(',', $sigHeader) as $item) {
        $item = trim($item);
        if (strpos($item, '=') === false) {
            continue;
        }
        [$k, $v] = explode('=', $item, 2);
        $parts[$k][] = $v;
    }
    $timestamp = $parts['t'][0] ?? '';
    $signatures = $parts['v1'] ?? [];
    if ($timestamp === '' || $signatures === []) {
        return ['ok' => false, 'error' => 'Invalid Stripe signature header'];
    }

    $signed = $timestamp . '.' . $payload;
    $expected = hash_hmac('sha256', $signed, $secret);
    $valid = false;
    foreach ($signatures as $sig) {
        if (hash_equals($expected, $sig)) {
            $valid = true;
            break;
        }
    }
    if (!$valid) {
        return ['ok' => false, 'error' => 'Signature mismatch'];
    }

    $data = json_decode($payload, true);
    return is_array($data) ? ['ok' => true, 'data' => $data] : ['ok' => false, 'error' => 'Invalid JSON'];
}
