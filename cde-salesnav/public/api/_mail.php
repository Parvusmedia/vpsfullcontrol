<?php
declare(strict_types=1);

/** Sales Navigator transactional mail — @companydataenrichment.com senders */

function cde_salesnav_mail_from_for(string $kind = 'general'): string
{
    $env = cde_salesnav_mail_read_env();
    if ($kind === 'export') {
        $from = trim((string) ($env['SALESNAV_MAIL_EXPORT_FROM'] ?? ''));
        if ($from !== '' && filter_var($from, FILTER_VALIDATE_EMAIL)) {
            return $from;
        }
        return 'export@companydataenrichment.com';
    }

    $from = trim((string) ($env['SALESNAV_MAIL_FROM'] ?? ''));
    if ($from !== '' && filter_var($from, FILTER_VALIDATE_EMAIL)) {
        return $from;
    }
    return 'hello@companydataenrichment.com';
}

function cde_salesnav_mail_from_name(): string
{
    $env = cde_salesnav_mail_read_env();
    $name = trim((string) ($env['SALESNAV_MAIL_FROM_NAME'] ?? ''));
    return $name !== '' ? $name : 'CompanyDataEnrichment';
}

/** @return array<string, string> */
function cde_salesnav_mail_read_env(): array
{
    static $cache = null;
    if (is_array($cache)) {
        return $cache;
    }
    $cache = [];
    if (function_exists('cde_unipile_read_env')) {
        $cache = cde_unipile_read_env();
        return $cache;
    }
    foreach ([dirname(__DIR__, 2) . '/private/cde/unipile.env', __DIR__ . '/unipile.env'] as $path) {
        if (!is_readable($path)) {
            continue;
        }
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $cache[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }
    return $cache;
}

function cde_salesnav_send_mail(string $to, string $subject, string $body, string $kind = 'general'): bool
{
    if ($to === '' || !filter_var($to, FILTER_VALIDATE_EMAIL)) {
        return false;
    }

    $from = cde_salesnav_mail_from_for($kind);
    $fromName = cde_salesnav_mail_from_name();
    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $safeBody = str_replace(["\r\n", "\r"], "\n", $body);

    $mailer = $kind === 'export' ? 'CompanyDataEnrichment-Export' : 'CompanyDataEnrichment';
    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        'From: ' . sprintf('"%s" <%s>', addcslashes($fromName, '"\\'), $from),
        'X-Mailer: ' . $mailer,
    ];

    return @mail($to, $encodedSubject, $safeBody, implode("\r\n", $headers));
}

function cde_salesnav_send_export_mail(string $to, string $subject, string $body): bool
{
    return cde_salesnav_send_mail($to, $subject, $body, 'export');
}

function cde_salesnav_send_general_mail(string $to, string $subject, string $body): bool
{
    return cde_salesnav_send_mail($to, $subject, $body, 'general');
}

/** @deprecated use cde_salesnav_mail_from_for() */
function cde_salesnav_mail_from(): string
{
    return cde_salesnav_mail_from_for('general');
}
