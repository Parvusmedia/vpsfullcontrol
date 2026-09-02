#!/usr/bin/env php
<?php
declare(strict_types=1);

/**
 * Grant export credits to a panel account by email (ops / admin).
 * Usage: grant-credits.php <email> <credits> [note]
 */
$email = strtolower(trim($argv[1] ?? ''));
$amount = (int) ($argv[2] ?? 0);
$note = trim(implode(' ', array_slice($argv, 3)));

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fwrite(STDERR, "Usage: grant-credits.php <email> <credits> [note]\n");
    exit(1);
}
if ($amount <= 0) {
    fwrite(STDERR, "Credits must be a positive integer.\n");
    exit(1);
}

$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_customers.php';
require $docroot . '/api/_credits.php';

$userId = cde_salesnav_user_id_for_email($email);
$before = cde_credits_get_balance($userId);
$ref = 'admin:grant:' . hash('sha256', $email . '|' . $amount . '|' . gmdate('Y-m-d\TH:i:s') . '|' . bin2hex(random_bytes(8)));
$meta = ['email' => $email, 'source' => 'grant-credits.php'];
if ($note !== '') {
    $meta['note'] = $note;
}

$after = cde_credits_add($userId, $amount, $ref, $meta);

echo "email={$email}\n";
echo "user_id={$userId}\n";
echo "granted={$amount}\n";
echo "balance_before={$before}\n";
echo "balance_after={$after}\n";
echo "ref={$ref}\n";
