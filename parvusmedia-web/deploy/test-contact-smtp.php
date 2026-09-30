<?php
/**
 * CLI-only SMTP check. Run on nextconvers, not via HTTP:
 * /opt/plesk/php/7.4/bin/php deploy/test-contact-smtp.php
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "CLI only\n");
    exit(1);
}

$httpdocs = '/var/www/vhosts/parvusmedia.com/httpdocs';
require $httpdocs . '/lib/smtp_mail.php';

$ok = parvus_web_send_mail(
    'hello@parvusmedia.com',
    'Parvus Media web — SMTP test',
    "Delivery test from the website contact stack.\nTime (UTC): " . gmdate('c') . "\nIf you received this, the ChatGPT Ads / homepage form can reach hello@parvusmedia.com.\n",
    'hello@parvusmedia.com'
);

fwrite(STDOUT, $ok ? "smtp_ok\n" : "smtp_fail\n");
exit($ok ? 0 : 1);
