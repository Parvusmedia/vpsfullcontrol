<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_credits.php';
require_once __DIR__ . '/_stripe.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

cde_salesnav_refresh_auth_cookie();

$billing = cde_credits_billing_enabled();
$balance = $billing ? cde_credits_get_balance() : 0;
$packs = cde_credits_packs();

$out = [];
foreach ($packs as $id => $pack) {
    $item = [
        'id' => $id,
        'credits' => $pack['credits'],
        'paid_base' => $pack['paid_base'],
        'bonus_credits' => $pack['bonus_credits'],
        'amount_cents' => $pack['amount_cents'],
        'price_eur' => number_format($pack['amount_cents'] / 100, 2, '.', ''),
        'label' => $pack['label'],
    ];
    $priceId = cde_stripe_price_id_for_pack((string) $id);
    if ($priceId !== '') {
        $item['stripe_price_id'] = $priceId;
    }
    $out[] = $item;
}

cde_json_response(200, [
    'ok' => true,
    'billing_enabled' => $billing,
    'balance' => $balance,
    'account_email' => cde_salesnav_session_email(),
    'packs' => $out,
    'min_eur' => CDE_CREDITS_MIN_EUR_CENTS / 100,
    'bonus_rule' => [
        'threshold_base_credits' => CDE_CREDITS_BONUS_THRESHOLD,
        'percent' => CDE_CREDITS_BONUS_PERCENT,
        'example' => '100 base credits → 120 in wallet (+20%)',
    ],
    'pricing' => [
        'basic_per_lead_eur' => 0.05,
        'enriched_extra_eur' => 0.02,
        'mail_extra_eur' => 0.09,
        'note' => 'Credits per export: Basic 1/lead; +Enriched +0.4/lead; +Mail +1 per work email found.',
    ],
]);
