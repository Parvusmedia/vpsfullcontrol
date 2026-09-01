<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_credits.php';
require __DIR__ . '/_stripe.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

if (!cde_credits_billing_enabled()) {
    cde_json_response(503, ['ok' => false, 'error' => 'Billing is not enabled yet.']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
}

$code = trim((string) ($payload['code'] ?? ''));
$packId = (string) ($payload['pack'] ?? '120');
$packs = cde_credits_packs();
if (!isset($packs[$packId])) {
    $packId = '120';
}
$pack = $packs[$packId];
$cfg = cde_stripe_config();
$userId = cde_salesnav_user_id();

$lookup = cde_stripe_lookup_promotion_code($code);
if (!$lookup['ok']) {
    cde_json_response(400, ['ok' => false, 'error' => $lookup['error'] ?? 'Invalid promotion code.']);
}

$promo = $lookup['promo'];
$coupon = $lookup['coupon'];
$promoId = (string) ($promo['id'] ?? '');
$promoCode = (string) ($promo['code'] ?? $code);

if (!cde_stripe_coupon_applies_to_product($coupon, $cfg['product_id'])) {
    cde_json_response(400, ['ok' => false, 'error' => 'This promotion code does not apply to SalesNav Export.']);
}

$restrictions = $promo['restrictions'] ?? [];
if (!empty($restrictions['first_time_transaction']) && cde_credits_user_has_paid_before($userId)) {
    cde_json_response(400, ['ok' => false, 'error' => 'This promotion code is only valid for first-time purchases.']);
}

if (cde_credits_has_redeemed_promo($userId, $promoId)) {
    cde_json_response(400, ['ok' => false, 'error' => 'You have already used this promotion code.']);
}

$amountCents = (int) $pack['amount_cents'];
if (!cde_stripe_coupon_is_full_discount($coupon, $amountCents)) {
    cde_json_response(400, [
        'ok' => false,
        'error' => 'This code gives a partial discount — complete checkout to pay the remaining balance.',
        'use_checkout' => true,
    ]);
}

$credits = (int) $pack['credits'];
$balance = cde_credits_add($userId, $credits, 'promo:' . $promoId, [
    'promo_code' => $promoCode,
    'pack_id' => $packId,
    'coupon_id' => (string) ($coupon['id'] ?? ''),
]);

cde_credits_mark_promo_redeemed($userId, $promoId, $promoCode);

cde_json_response(200, [
    'ok' => true,
    'credits_added' => $credits,
    'balance' => $balance,
    'message' => 'Promotion applied. You can connect LinkedIn now.',
]);
