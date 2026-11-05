<?php

declare(strict_types=1);

/** @return array{host:string,port:int,secure:string,user:string,pass:string}|null */
function ngaged_smtp_config(): ?array
{
    $env = gaggle_demo_load_env();
    $host = trim($env['NGAGED_SMTP_HOST'] ?? '');
    if ($host === '') {
        return null;
    }
    return [
        'host' => $host,
        'port' => (int) ($env['NGAGED_SMTP_PORT'] ?? 587),
        'secure' => strtolower(trim($env['NGAGED_SMTP_SECURE'] ?? 'tls')),
        'user' => trim($env['NGAGED_SMTP_USER'] ?? ''),
        'pass' => (string) ($env['NGAGED_SMTP_PASSWORD'] ?? ''),
    ];
}

function ngaged_mail_transport_label(): string
{
    if (ngaged_smtp_config() !== null) {
        return 'smtp';
    }
    return function_exists('mail') ? 'php-mail' : 'unavailable';
}

function ngaged_parse_mailbox(string $fromHeader): array
{
    if (preg_match('/<([^>]+)>/', $fromHeader, $m)) {
        return ['email' => trim($m[1]), 'name' => trim(preg_replace('/<[^>]+>/', '', $fromHeader))];
    }
    return ['email' => trim($fromHeader), 'name' => ''];
}

function ngaged_smtp_read($fp): string
{
    $data = '';
    while ($line = fgets($fp, 515)) {
        $data .= $line;
        if (isset($line[3]) && $line[3] === ' ') {
            break;
        }
    }
    return $data;
}

function ngaged_smtp_expect($fp, array $codes): bool
{
    $resp = ngaged_smtp_read($fp);
    $code = (int) substr($resp, 0, 3);
    return in_array($code, $codes, true);
}

function ngaged_smtp_cmd($fp, string $cmd, array $expectCodes): bool
{
    fwrite($fp, $cmd . "\r\n");
    return ngaged_smtp_expect($fp, $expectCodes);
}

/** @return array{ok:bool,error?:string} */
function ngaged_send_mail_smtp(string $to, string $subject, string $htmlBody, string $textBody, string $fromHeader): array
{
    $cfg = ngaged_smtp_config();
    if ($cfg === null) {
        return ['ok' => false, 'error' => 'SMTP no configurado'];
    }
    if ($cfg['user'] === '' || $cfg['pass'] === '') {
        return ['ok' => false, 'error' => 'Faltan NGAGED_SMTP_USER o NGAGED_SMTP_PASSWORD'];
    }

    $from = ngaged_parse_mailbox($fromHeader);
    $fromEmail = $from['email'] !== '' ? $from['email'] : $cfg['user'];

    $host = $cfg['host'];
    $port = $cfg['port'] > 0 ? $cfg['port'] : 587;
    $fp = @stream_socket_client('tcp://' . $host . ':' . $port, $errno, $errstr, 20);
    if (!$fp) {
        return ['ok' => false, 'error' => 'No se pudo conectar a SMTP: ' . $errstr];
    }
    stream_set_timeout($fp, 20);

    if (!ngaged_smtp_expect($fp, [220])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: respuesta inicial inválida'];
    }
    $ehloHost = 'ngaged.local';
    if (!ngaged_smtp_cmd($fp, 'EHLO ' . $ehloHost, [250])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: EHLO falló'];
    }

    if ($cfg['secure'] === 'tls') {
        if (!ngaged_smtp_cmd($fp, 'STARTTLS', [220])) {
            fclose($fp);
            return ['ok' => false, 'error' => 'SMTP: STARTTLS no aceptado'];
        }
        $crypto = @stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT);
        if (!$crypto) {
            fclose($fp);
            return ['ok' => false, 'error' => 'SMTP: no se pudo negociar TLS'];
        }
        if (!ngaged_smtp_cmd($fp, 'EHLO ' . $ehloHost, [250])) {
            fclose($fp);
            return ['ok' => false, 'error' => 'SMTP: EHLO post-TLS falló'];
        }
    }

    if (!ngaged_smtp_cmd($fp, 'AUTH LOGIN', [334])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: AUTH LOGIN rechazado'];
    }
    if (!ngaged_smtp_cmd($fp, base64_encode($cfg['user']), [334])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: usuario rechazado'];
    }
    if (!ngaged_smtp_cmd($fp, base64_encode($cfg['pass']), [235])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: contraseña rechazada'];
    }

    if (!ngaged_smtp_cmd($fp, 'MAIL FROM:<' . $fromEmail . '>', [250])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: MAIL FROM falló'];
    }
    if (!ngaged_smtp_cmd($fp, 'RCPT TO:<' . $to . '>', [250, 251])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: RCPT TO falló'];
    }
    if (!ngaged_smtp_cmd($fp, 'DATA', [354])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: DATA falló'];
    }

    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $boundary = 'ngaged_' . bin2hex(random_bytes(8));
    $message =
        'From: ' . $fromHeader . "\r\n"
        . 'To: ' . $to . "\r\n"
        . 'Subject: ' . $encodedSubject . "\r\n"
        . 'MIME-Version: 1.0' . "\r\n"
        . 'Content-Type: multipart/alternative; boundary="' . $boundary . '"' . "\r\n"
        . "\r\n"
        . '--' . $boundary . "\r\n"
        . "Content-Type: text/plain; charset=UTF-8\r\n\r\n"
        . $textBody . "\r\n"
        . '--' . $boundary . "\r\n"
        . "Content-Type: text/html; charset=UTF-8\r\n\r\n"
        . $htmlBody . "\r\n"
        . '--' . $boundary . "--\r\n";

    fwrite($fp, $message . "\r\n.\r\n");
    if (!ngaged_smtp_expect($fp, [250])) {
        fclose($fp);
        return ['ok' => false, 'error' => 'SMTP: envío de mensaje falló'];
    }

    ngaged_smtp_cmd($fp, 'QUIT', [221]);
    fclose($fp);
    return ['ok' => true];
}
