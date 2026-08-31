<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_credits.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$billing = cde_credits_billing_enabled();
$balance = $billing ? cde_credits_get_balance() : 0;
$packs = cde_credits_packs();

$out = [];
foreach ($packs as $id => $pack) {
    $out[] = [
        'id' => $id,
        'credits' => $pack['credits'],
        'amount_cents' => $pack['amount_cents'],
        'price_eur' => number_format($pack['amount_cents'] / 100, 2, '.', ''),
    ];
}

cde_json_response(200, [
    'ok' => true,
    'billing_enabled' => $billing,
    'balance' => $balance,
    'packs' => $out,
]);
