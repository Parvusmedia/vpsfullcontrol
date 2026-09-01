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
    if (is_array($session)) {
        cde_stripe_apply_checkout_credits($session, false);
    }
}

http_response_code(200);
echo 'ok';
