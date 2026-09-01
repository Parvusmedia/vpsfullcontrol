#!/usr/bin/env php
<?php
/**
 * Live Stripe E2E: create checkout session → simulate signed webhook → verify wallet.
 * Run on production only: php deploy/test-stripe-webhook-e2e.php
 */
declare(strict_types=1);

$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
$private = '/var/www/vhosts/companydataenrichment.com/private/cde';

require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_stripe.php';
require $docroot . '/api/_credits.php';

$userId = cde_salesnav_user_id();
$before = cde_credits_get_balance($userId);
$packId = '240';
$packs = cde_credits_packs();
$pack = $packs[$packId];
$result = cde_stripe_create_checkout_session($userId, $packId);
$sessionId = $result['session_id'];
$credits = (int) $pack['credits'];

echo "user_id={$userId}\n";
echo "balance_before={$before}\n";
echo "session_id={$sessionId}\n";
echo "pack={$packId} credits={$credits}\n";

$event = [
    'id' => 'evt_e2e_' . bin2hex(random_bytes(8)),
    'type' => 'checkout.session.completed',
    'data' => [
        'object' => [
            'id' => $sessionId,
            'metadata' => [
                'user_id' => $userId,
                'pack_id' => $packId,
                'credits' => (string) $credits,
                'paid_base' => (string) $pack['paid_base'],
                'bonus_credits' => (string) $pack['bonus_credits'],
            ],
            'client_reference_id' => $userId,
            'amount_total' => $pack['amount_cents'],
        ],
    ],
];

$payload = json_encode($event, JSON_UNESCAPED_SLASHES);
$env = cde_credits_read_env();
$secret = $env['STRIPE_WEBHOOK_SECRET'] ?? '';
if ($secret === '') {
    fwrite(STDERR, "Missing STRIPE_WEBHOOK_SECRET\n");
    exit(1);
}

$timestamp = time();
$signed = hash_hmac('sha256', $timestamp . '.' . $payload, $secret);
$sigHeader = 't=' . $timestamp . ',v1=' . $signed;

$ch = curl_init('https://companydataenrichment.com/api/salesnav-stripe-webhook.php');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Stripe-Signature: ' . $sigHeader,
    ],
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_TIMEOUT => 30,
]);
$resp = curl_exec($ch);
$code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "webhook_http={$code} body=" . trim((string) $resp) . "\n";

$after = cde_credits_get_balance($userId);
echo "balance_after={$after}\n";
echo "delta=" . ($after - $before) . "\n";

if ($code !== 200 || $after <= $before) {
    exit(2);
}

// Idempotency: second webhook must not double-credit
$timestamp2 = time();
$signed2 = hash_hmac('sha256', $timestamp2 . '.' . $payload, $secret);
curl_setopt_array($ch = curl_init('https://companydataenrichment.com/api/salesnav-stripe-webhook.php'), [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Stripe-Signature: ' . ('t=' . $timestamp2 . ',v1=' . $signed2),
    ],
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_TIMEOUT => 30,
]);
curl_exec($ch);
curl_close($ch);
$after2 = cde_credits_get_balance($userId);
echo "balance_after_dup={$after2}\n";
echo ($after2 === $after ? "idempotent_ok\n" : "idempotent_fail\n");
exit($after2 === $after ? 0 : 3);
