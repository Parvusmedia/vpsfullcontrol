<?php
declare(strict_types=1);

$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_icypeas.php';

$to = $argv[1] ?? '';
if ($to === '') {
    fwrite(STDERR, "Usage: test-icypeas-mail.php [optional-notify-email]\n");
}

if (!cde_icypeas_enabled()) {
    echo json_encode(['ok' => false, 'error' => 'Icypeas not configured'], JSON_PRETTY_PRINT) . "\n";
    exit(1);
}

$result = cde_icypeas_find_email('Pierre', 'Landoin', 'icypeas.com');
echo json_encode(['ok' => true, 'test' => $result], JSON_PRETTY_PRINT) . "\n";
exit(empty($result['work_email']) ? 2 : 0);
