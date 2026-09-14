<?php
declare(strict_types=1);

require_once __DIR__ . '/env.php';

/**
 * Send mail through Zoho SMTP (SPF for parvusmedia.com does not include this VPS).
 */
function parvus_web_send_mail(string $to, string $subject, string $body, string $replyTo = ''): bool
{
    $env = parvus_web_read_env('mail.env');
    $host = trim((string)($env['SMTP_HOST'] ?? 'smtppro.zoho.com'));
    $port = (int)($env['SMTP_PORT'] ?? 587);
    $user = trim((string)($env['SMTP_USER'] ?? ''));
    $pass = (string)($env['SMTP_PASS'] ?? '');
    $from = trim((string)($env['MAIL_FROM'] ?? $user));
    $fromName = 'Parvus Media';
    $toAddr = trim((string)($env['MAIL_TO'] ?? $to));

    if ($user === '' || $pass === '' || $from === '' || !filter_var($toAddr, FILTER_VALIDATE_EMAIL)) {
        return false;
    }
    if ($replyTo !== '' && !filter_var($replyTo, FILTER_VALIDATE_EMAIL)) {
        $replyTo = '';
    }

    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $messageId = sprintf('<%s@parvusmedia.com>', bin2hex(random_bytes(16)));
    $date = gmdate('D, d M Y H:i:s') . ' +0000';
    $safeBody = str_replace(["\r\n", "\r"], "\n", $body);
    $safeBody = str_replace("\n", "\r\n", $safeBody);
    if (strpos($safeBody, "\r\n.\r\n") !== false) {
        $safeBody = str_replace("\r\n.\r\n", "\r\n..\r\n", $safeBody);
    }

    $fromHeader = sprintf('"%s" <%s>', addcslashes($fromName, '"\\'), $from);
    $headers = [
        'Date: ' . $date,
        'From: ' . $fromHeader,
        'To: <' . $toAddr . '>',
        'Subject: ' . $encodedSubject,
        'Message-ID: ' . $messageId,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        'X-Mailer: ParvusMedia-web',
    ];
    if ($replyTo !== '') {
        $headers[] = 'Reply-To: <' . $replyTo . '>';
    }

    $data = implode("\r\n", $headers) . "\r\n\r\n" . $safeBody . "\r\n";

    $errno = 0;
    $errstr = '';
    $fp = @stream_socket_client(
        'tcp://' . $host . ':' . $port,
        $errno,
        $errstr,
        20,
        STREAM_CLIENT_CONNECT
    );
    if ($fp === false) {
        return false;
    }
    stream_set_timeout($fp, 20);

    try {
        parvus_smtp_expect($fp, 220);
        parvus_smtp_cmd($fp, 'EHLO parvusmedia.com', 250);
        parvus_smtp_cmd($fp, 'STARTTLS', 220);
        $crypto = @stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLSv1_2_CLIENT);
        if ($crypto !== true) {
            $crypto = @stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT);
        }
        if ($crypto !== true) {
            throw new RuntimeException('tls');
        }
        parvus_smtp_cmd($fp, 'EHLO parvusmedia.com', 250);
        parvus_smtp_cmd($fp, 'AUTH LOGIN', 334);
        parvus_smtp_cmd($fp, base64_encode($user), 334);
        parvus_smtp_cmd($fp, base64_encode($pass), 235);
        parvus_smtp_cmd($fp, 'MAIL FROM:<' . $from . '>', 250);
        parvus_smtp_cmd($fp, 'RCPT TO:<' . $toAddr . '>', 250);
        parvus_smtp_cmd($fp, 'DATA', 354);
        fwrite($fp, $data);
        if (substr($data, -2) !== "\r\n") {
            fwrite($fp, "\r\n");
        }
        parvus_smtp_cmd($fp, '.', 250);
        parvus_smtp_cmd($fp, 'QUIT', 221);
        fclose($fp);
        return true;
    } catch (Throwable $e) {
        error_log('parvusmedia-web smtp failed: ' . $e->getMessage());
        fclose($fp);
        return false;
    }
}

/**
 * @param resource $fp
 */
function parvus_smtp_cmd($fp, string $line, int $expect): void
{
    fwrite($fp, $line . "\r\n");
    parvus_smtp_expect($fp, $expect);
}

/**
 * @param resource $fp
 */
function parvus_smtp_expect($fp, int $expect): void
{
    $last = '';
    while (($row = fgets($fp, 2048)) !== false) {
        $last = $row;
        if (isset($row[3]) && $row[3] === ' ') {
            break;
        }
    }
    if ($last === '' || (int)substr($last, 0, 3) !== $expect) {
        throw new RuntimeException('smtp expect ' . $expect . ' got ' . substr($last, 0, 3));
    }
}
