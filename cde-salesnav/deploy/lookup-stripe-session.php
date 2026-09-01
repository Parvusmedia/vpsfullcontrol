#!/usr/bin/env php
<?php
declare(strict_types=1);

require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_bootstrap.php';
require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_stripe.php';

$sessions = array_slice($argv, 1);
if ($sessions === []) {
    $sessions = [
        'cs_live_b1cHA53p31gB5BnqTJd9ipCtBQp6PthgQLtJovKNAIZfojm5SDTDM41HU3',
        'cs_live_b1znw1IlcIsncyhrqXVApYb1UKeFKDyD9db31B80MnQJuAcjeNhvu13biP',
    ];
}

foreach ($sessions as $sid) {
    $resp = cde_stripe_retrieve_checkout_session($sid);
    if (!$resp['ok']) {
        echo $sid . "\tERROR\t" . ($resp['error'] ?? '') . "\n";
        continue;
    }
    $s = $resp['data'];
    $email = cde_stripe_checkout_email($s);
    $uid = (string) ($s['metadata']['user_id'] ?? $s['client_reference_id'] ?? '');
    $paid = (string) ($s['payment_status'] ?? '');
    $amt = (int) ($s['amount_total'] ?? 0);
    $created = (string) ($s['created'] ?? '');
    echo implode("\t", [$sid, $paid, $email, $uid, (string) $amt, $created]) . "\n";
}
