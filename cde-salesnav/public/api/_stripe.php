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
    $productId = $env['STRIPE_PRODUCT_ID'] ?? getenv('STRIPE_PRODUCT_ID') ?: 'prod_VB9BUSTFvzzBRm';

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
        'product_id' => $productId,
    ];
}

/** Stripe Price ID for a pack (env override: STRIPE_PRICE_ID_120, or STRIPE_PRICE_ID for min pack). */
function cde_stripe_price_id_for_pack(string $packId): string
{
    $env = cde_credits_read_env();
    $specific = $env['STRIPE_PRICE_ID_' . $packId] ?? getenv('STRIPE_PRICE_ID_' . $packId) ?: '';
    if ($specific !== '') {
        return $specific;
    }
    if ($packId === '120') {
        return $env['STRIPE_PRICE_ID'] ?? getenv('STRIPE_PRICE_ID') ?: 'price_1UAnliL0sc6a4STMwyYdMPF4';
    }
    return '';
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

function cde_stripe_get(string $path, array $query = []): array
{
    $cfg = cde_stripe_config();
    $url = 'https://api.stripe.com/v1/' . ltrim($path, '/');
    if ($query !== []) {
        $url .= '?' . http_build_query($query);
    }
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            'Authorization: Bearer ' . $cfg['secret_key'],
        ],
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

/** @return array{ok: bool, error?: string, promo?: array, coupon?: array} */
function cde_stripe_lookup_promotion_code(string $code): array
{
    $code = trim($code);
    if ($code === '') {
        return ['ok' => false, 'error' => 'Enter a promotion code.'];
    }

    $resp = cde_stripe_get('promotion_codes', [
        'code' => $code,
        'limit' => 1,
        'expand' => ['data.coupon.applies_to'],
    ]);
    if (!$resp['ok']) {
        return ['ok' => false, 'error' => $resp['error'] ?? 'Could not validate promotion code.'];
    }

    $promo = ($resp['data']['data'][0] ?? null);
    if (!is_array($promo)) {
        return ['ok' => false, 'error' => 'This promotion code is invalid.'];
    }
    if (empty($promo['active'])) {
        return ['ok' => false, 'error' => 'This promotion code is no longer active.'];
    }

    $coupon = $promo['coupon'] ?? [];
    if (!is_array($coupon) || empty($coupon['valid'])) {
        return ['ok' => false, 'error' => 'This promotion code is invalid.'];
    }

    $max = $promo['max_redemptions'] ?? null;
    $used = (int) ($promo['times_redeemed'] ?? 0);
    if ($max !== null && $used >= (int) $max) {
        return ['ok' => false, 'error' => 'This promotion code has reached its redemption limit.'];
    }

    $expires = (int) ($promo['expires_at'] ?? 0);
    if ($expires > 0 && $expires < time()) {
        return ['ok' => false, 'error' => 'This promotion code has expired.'];
    }

    return ['ok' => true, 'promo' => $promo, 'coupon' => $coupon];
}

function cde_stripe_coupon_applies_to_product(array $coupon, string $productId): bool
{
    $applies = $coupon['applies_to']['products'] ?? null;
    if (!is_array($applies) || $applies === []) {
        return true;
    }
    return in_array($productId, $applies, true);
}

/** True when Stripe Checkout payment mode cannot accept this coupon (100% off → €0 total). */
function cde_stripe_coupon_is_full_discount(array $coupon, int $amountCents): bool
{
    $percent = (float) ($coupon['percent_off'] ?? 0);
    if ($percent >= 100) {
        return true;
    }
    $amountOff = (int) ($coupon['amount_off'] ?? 0);
    return $amountOff >= $amountCents && $amountCents > 0;
}

function cde_stripe_create_checkout_session(string $userId, string $packId): array
{
    $packs = cde_credits_packs();
    if (!isset($packs[$packId])) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid credit pack.']);
    }
    $pack = $packs[$packId];
    $cfg = cde_stripe_config();

    $paidBase = (int) ($pack['paid_base'] ?? $pack['credits']);
    $bonus = (int) ($pack['bonus_credits'] ?? 0);
    $total = (int) $pack['credits'];

    $env = cde_credits_read_env();
    // Stripe Checkout payment mode rejects 100% off (€0 total). Partial codes only.
    $allowPromo = ($env['STRIPE_ALLOW_PROMOTION_CODES'] ?? '0') === '1';

    $fields = [
        'mode' => 'payment',
        'success_url' => $cfg['origin'] . '/salesnav/?credits=1',
        'cancel_url' => $cfg['origin'] . '/salesnav/?credits=0',
        'client_reference_id' => $userId,
        'metadata[user_id]' => $userId,
        'metadata[pack_id]' => $packId,
        'metadata[credits]' => (string) $total,
        'metadata[paid_base]' => (string) $paidBase,
        'metadata[bonus_credits]' => (string) $bonus,
        'metadata[stripe_product_id]' => $cfg['product_id'],
        'line_items[0][quantity]' => '1',
    ];

    if ($allowPromo) {
        $fields['allow_promotion_codes'] = 'true';
    }

    $priceId = cde_stripe_price_id_for_pack($packId);
    if ($priceId !== '') {
        $fields['line_items[0][price]'] = $priceId;
    } else {
        // Fallback for packs without a catalog Price — product only, no product_data mix.
        $fields['line_items[0][price_data][currency]'] = 'eur';
        $fields['line_items[0][price_data][unit_amount]'] = (string) $pack['amount_cents'];
        $fields['line_items[0][price_data][product]'] = $cfg['product_id'];
        $priceId = '';
    }

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
        'stripe_price_id' => $priceId !== '' ? $priceId : null,
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
