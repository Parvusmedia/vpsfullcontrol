<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_stripe.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo 'Method not allowed';
    exit;
}

$payload = file_get_contents('php://input') ?: '';
$sig = (string) ($_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '');
$verified = cde_stripe_verify_webhook($payload, $sig);

if (!$verified['ok']) {
    http_response_code(400);
    echo $verified['error'] ?? 'Invalid webhook';
    exit;
}

$event = $verified['data'];
$type = (string) ($event['type'] ?? '');

if ($type === 'checkout.session.completed') {
    $session = $event['data']['object'] ?? [];
    if (!is_array($session)) {
        http_response_code(200);
        echo 'ok';
        exit;
    }
    $userId = (string) ($session['metadata']['user_id'] ?? $session['client_reference_id'] ?? '');
    $credits = (int) ($session['metadata']['credits'] ?? 0);
    $sessionId = (string) ($session['id'] ?? '');
    if ($userId !== '' && $credits > 0 && $sessionId !== '') {
        cde_credits_add($userId, $credits, 'stripe:' . $sessionId, [
            'pack_id' => (string) ($session['metadata']['pack_id'] ?? ''),
            'paid_base' => (int) ($session['metadata']['paid_base'] ?? 0),
            'bonus_credits' => (int) ($session['metadata']['bonus_credits'] ?? 0),
            'amount_total' => (int) ($session['amount_total'] ?? 0),
        ]);
    }
}

http_response_code(200);
echo 'ok';
