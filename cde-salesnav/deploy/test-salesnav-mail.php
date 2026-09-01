<?php
declare(strict_types=1);

require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_bootstrap.php';
require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_unipile.php';
require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_mail.php';

$to = $argv[1] ?? '';
$kind = $argv[2] ?? 'export';
if ($to === '') {
    fwrite(STDERR, "Usage: test-salesnav-mail.php recipient [export|general]\n");
    exit(1);
}

$ok = cde_salesnav_send_mail(
    $to,
    'Sales Navigator mail FROM test (' . $kind . ')',
    "Hello,\n\nTest notification.\n\nFrom: " . cde_salesnav_mail_from_for($kind) . "\n",
    $kind
);
echo json_encode(['ok' => $ok, 'kind' => $kind, 'from' => cde_salesnav_mail_from_for($kind)], JSON_PRETTY_PRINT) . "\n";
