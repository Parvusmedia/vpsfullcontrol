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

function cde_salesnav_mail_message_id(string $from): string
{
    $domain = 'companydataenrichment.com';
    if (str_contains($from, '@')) {
        $parts = explode('@', $from, 2);
        if (!empty($parts[1])) {
            $domain = $parts[1];
        }
    }

    return sprintf('<%s@%s>', bin2hex(random_bytes(16)), $domain);
}

function cde_salesnav_mail_build_headers(string $from, string $fromName, string $mailer, string $replyTo, string $contentType): array
{
    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: ' . $contentType,
        'Content-Transfer-Encoding: 8bit',
        'Date: ' . gmdate('D, d M Y H:i:s') . ' +0000',
        'Message-ID: ' . cde_salesnav_mail_message_id($from),
        'From: ' . sprintf('"%s" <%s>', addcslashes($fromName, '"\\'), $from),
        'Reply-To: <' . ($replyTo !== '' && filter_var($replyTo, FILTER_VALIDATE_EMAIL) ? $replyTo : $from) . '>',
        'X-Mailer: ' . $mailer,
        'Auto-Submitted: auto-generated',
        'X-Auto-Response-Suppress: All',
    ];

    return $headers;
}

function cde_salesnav_mail_build_multipart_body(string $textBody, string $htmlBody): array
{
    $boundary = 'cde_' . bin2hex(random_bytes(12));
    $textBody = str_replace(["\r\n", "\r"], "\n", $textBody);
    $htmlBody = str_replace(["\r\n", "\r"], "\n", $htmlBody);

    $body = implode("\r\n", [
        'This is a multi-part message in MIME format.',
        '',
        '--' . $boundary,
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        '',
        $textBody,
        '',
        '--' . $boundary,
        'Content-Type: text/html; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        '',
        $htmlBody,
        '',
        '--' . $boundary . '--',
        '',
    ]);

    return [$body, 'multipart/alternative; boundary="' . $boundary . '"'];
}

function cde_salesnav_send_mail(
    string $to,
    string $subject,
    string $body,
    string $kind = 'general',
    string $replyTo = '',
    ?string $htmlBody = null
): bool {
    if ($to === '' || !filter_var($to, FILTER_VALIDATE_EMAIL)) {
        return false;
    }

    $from = cde_salesnav_mail_from_for($kind);
    $fromName = cde_salesnav_mail_from_name();
    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $safeBody = str_replace(["\r\n", "\r"], "\n", $body);
    $mailer = $kind === 'export' ? 'CompanyDataEnrichment-Export' : 'CompanyDataEnrichment';

    if ($htmlBody !== null && trim($htmlBody) !== '') {
        [$safeBody, $contentType] = cde_salesnav_mail_build_multipart_body($safeBody, $htmlBody);
    } else {
        $contentType = 'text/plain; charset=UTF-8';
    }

    $headers = cde_salesnav_mail_build_headers($from, $fromName, $mailer, $replyTo, $contentType);
    $params = '-f' . escapeshellarg($from);

    return @mail($to, $encodedSubject, $safeBody, implode("\r\n", $headers), $params);
}

function cde_salesnav_send_export_mail(string $to, string $subject, string $body, string $replyTo = '', ?string $htmlBody = null): bool
{
    return cde_salesnav_send_mail($to, $subject, $body, 'export', $replyTo, $htmlBody);
}

function cde_salesnav_send_general_mail(string $to, string $subject, string $body, string $replyTo = '', ?string $htmlBody = null): bool
{
    return cde_salesnav_send_mail($to, $subject, $body, 'general', $replyTo, $htmlBody);
}

/** @deprecated use cde_salesnav_mail_from_for() */
function cde_salesnav_mail_from(): string
{
    return cde_salesnav_mail_from_for('general');
}
