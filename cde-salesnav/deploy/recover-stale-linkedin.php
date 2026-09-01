#!/usr/bin/env php
<?php
/**
 * One-off: clear invalid_at when Unipile seat is already alive.
 * Usage: php recover-stale-linkedin.php [email]
 */
declare(strict_types=1);

$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_customers.php';

$email = strtolower(trim($argv[1] ?? 'emiliano@parvusmedia.com'));
$userId = cde_salesnav_user_id_for_email($email);
$stored = cde_salesnav_load_accounts()[$userId] ?? null;

if (!is_array($stored)) {
    fwrite(STDERR, "No stored account for {$email}\n");
    exit(1);
}

echo "Before: " . json_encode($stored, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";

if (empty($stored['invalid_at'])) {
    echo "Already valid — nothing to do.\n";
    exit(0);
}

$seat = cde_salesnav_find_reconnectable_seat($userId);
if ($seat === null) {
    fwrite(STDERR, "No reconnectable seat found.\n");
    exit(1);
}

echo "Seat: {$seat}, alive=" . (cde_salesnav_is_account_alive($seat) ? 'yes' : 'no') . "\n";

if (!cde_salesnav_try_recover_stale_account($userId)) {
    fwrite(STDERR, "Recovery failed.\n");
    exit(1);
}

$after = cde_salesnav_load_accounts()[$userId] ?? [];
echo "After: " . json_encode($after, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";
echo "OK\n";
