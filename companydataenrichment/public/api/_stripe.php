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
    if ($packId === '240') {
        return $env['STRIPE_PRICE_ID'] ?? getenv('STRIPE_PRICE_ID') ?: 'price_1UAnliL0sc6a4STMwyYdMPF4';
    }
    return '';
}

function cde_stripe_request(string $method, string $path, array $fields): array
{
    $cfg = cde_stripe_config();
    $method = strtoupper($method);
    $ch = curl_init('https://api.stripe.com/v1/' . ltrim($path, '/'));
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => [
            'Authorization: Bearer ' . $cfg['secret_key'],
        ],
        CURLOPT_TIMEOUT => 30,
    ];
    if ($method !== 'GET' && $fields !== []) {
        $opts[CURLOPT_HTTPHEADER][] = 'Content-Type: application/x-www-form-urlencoded';
        $opts[CURLOPT_POSTFIELDS] = http_build_query($fields);
    }
    curl_setopt_array($ch, $opts);
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

function cde_stripe_create_checkout_session(string $userId, string $packId, string $customerEmail = ''): array
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
    $allowPromo = ($env['STRIPE_ALLOW_PROMOTION_CODES'] ?? '1') !== '0';

    $customerEmail = strtolower(trim($customerEmail));
    if ($customerEmail !== '' && !filter_var($customerEmail, FILTER_VALIDATE_EMAIL)) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid email address.']);
    }

    $fields = [
        'mode' => 'payment',
        'success_url' => $cfg['origin'] . '/salesnav/stripe-callback.html?credits=1&session_id={CHECKOUT_SESSION_ID}',
        'cancel_url' => $cfg['origin'] . '/salesnav/stripe-callback.html?credits=0',
        'client_reference_id' => $userId,
        'metadata[user_id]' => $userId,
        'metadata[pack_id]' => $packId,
        'metadata[credits]' => (string) $total,
        'metadata[paid_base]' => (string) $paidBase,
        'metadata[bonus_credits]' => (string) $bonus,
        'metadata[stripe_product_id]' => $cfg['product_id'],
        'line_items[0][quantity]' => '1',
    ];

    if ($customerEmail !== '') {
        $fields['customer_email'] = $customerEmail;
        $fields['metadata[customer_email]'] = $customerEmail;
    }

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

function cde_stripe_checkout_email(array $session): string
{
    return strtolower(trim((string) (
        $session['customer_details']['email']
        ?? $session['customer_email']
        ?? $session['metadata']['customer_email']
        ?? ''
    )));
}

function cde_stripe_retrieve_checkout_session(string $sessionId): array
{
    $sessionId = trim($sessionId);
    if ($sessionId === '' || !preg_match('/^cs_/', $sessionId)) {
        return ['ok' => false, 'error' => 'Invalid checkout session.'];
    }
    return cde_stripe_request('GET', 'checkout/sessions/' . rawurlencode($sessionId), []);
}

/**
 * Credit wallet for a paid checkout session (idempotent). Optionally bind browser session to email.
 *
 * @return array{ok: bool, balance?: int, credits?: int, email?: string, user_id?: string, error?: string}
 */
function cde_stripe_apply_checkout_credits(array $session, bool $bindBrowserSession = false): array
{
    $sessionId = (string) ($session['id'] ?? '');
    $credits = (int) ($session['metadata']['credits'] ?? 0);
    $paymentStatus = (string) ($session['payment_status'] ?? '');
    if ($sessionId === '' || $credits <= 0) {
        return ['ok' => false, 'error' => 'Invalid checkout session.'];
    }
    if ($paymentStatus !== 'paid') {
        return ['ok' => false, 'error' => 'Payment not completed yet.'];
    }

    $email = cde_stripe_checkout_email($session);
    $metaUserId = (string) ($session['metadata']['user_id'] ?? $session['client_reference_id'] ?? '');

    if ($email !== '') {
        $userId = cde_salesnav_user_id_for_email($email);
        if ($metaUserId !== '' && $metaUserId !== $userId) {
            cde_credits_merge_wallets($metaUserId, $userId);
        }
    } else {
        $userId = $metaUserId !== '' ? $metaUserId : cde_salesnav_user_id();
    }

    $balance = cde_credits_add($userId, $credits, 'stripe:' . $sessionId, [
        'pack_id' => (string) ($session['metadata']['pack_id'] ?? ''),
        'paid_base' => (int) ($session['metadata']['paid_base'] ?? 0),
        'bonus_credits' => (int) ($session['metadata']['bonus_credits'] ?? 0),
        'amount_total' => (int) ($session['amount_total'] ?? 0),
        'email' => $email,
    ]);

    return [
        'ok' => true,
        'balance' => $balance,
        'credits' => $credits,
        'email' => $email,
        'user_id' => $userId,
    ];
}
