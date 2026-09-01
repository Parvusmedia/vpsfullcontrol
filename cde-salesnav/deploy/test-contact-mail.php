<?php
declare(strict_types=1);

require '/var/www/vhosts/companydataenrichment.com/httpdocs/api/_bootstrap.php';

$to = $argv[1] ?? '';
if ($to === '') {
    fwrite(STDERR, "Usage: test-contact-mail.php recipient\n");
    exit(1);
}

$result = cde_send_contact_mail(
    cde_load_mail_config()['to'],
    'CDE contact mail test',
    "Test contact notification via cde_send_contact_mail()\nTime: " . gmdate('c') . "\n",
    $to
);

echo json_encode([
    'ok' => !empty($result['ok']),
    'error' => $result['error'] ?? null,
    'mail_to' => cde_load_mail_config()['to'],
    'transport' => cde_load_mail_config()['transport'] ?? 'local',
], JSON_PRETTY_PRINT) . "\n";

exit(empty($result['ok']) ? 1 : 0);
