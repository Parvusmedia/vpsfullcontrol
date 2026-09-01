#!/usr/bin/env php
<?php
declare(strict_types=1);

require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_bootstrap.php';
require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_credits.php';

$email = strtolower(trim($argv[1] ?? ''));
$fromUserId = trim($argv[2] ?? '');
if ($email === '' || $fromUserId === '') {
    fwrite(STDERR, "Usage: php link-stripe-wallet-to-email.php <email> <anonymous_user_id>\n");
    exit(1);
}

$toUserId = cde_salesnav_user_id_for_email($email);
$fromBal = cde_credits_get_balance($fromUserId);
$toBalBefore = cde_credits_get_balance($toUserId);

if ($fromBal <= 0) {
    echo "nothing_to_merge from_balance={$fromBal}\n";
    exit(0);
}

cde_credits_merge_wallets($fromUserId, $toUserId);
$toBalAfter = cde_credits_get_balance($toUserId);

cde_credits_append_ledger([
    'user_id' => $toUserId,
    'delta' => 0,
    'balance' => $toBalAfter,
    'ref' => 'admin:link_email:' . hash('sha256', $email . '|' . $fromUserId),
    'meta' => [
        'email' => $email,
        'from_user_id' => $fromUserId,
        'merged_balance' => $fromBal,
        'note' => 'Manual link of pre-email Stripe payment to account',
    ],
]);

echo "email={$email}\n";
echo "from_user_id={$fromUserId}\n";
echo "to_user_id={$toUserId}\n";
echo "merged={$fromBal}\n";
echo "balance_before={$toBalBefore}\n";
echo "balance_after={$toBalAfter}\n";
