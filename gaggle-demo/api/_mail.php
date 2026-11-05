<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_tokens.php';
require_once __DIR__ . '/_smtp.php';

function ngaged_mail_from(): string
{
    $file = gaggle_demo_load_env();
    return trim($file['NGAGED_MAIL_FROM'] ?? 'Ngaged <noreply@pmediaplus.com>');
}

function ngaged_send_mail(string $to, string $subject, string $htmlBody, string $textBody = ''): bool
{
    if ($textBody === '') {
        $textBody = strip_tags(str_replace(['<br>', '<br/>', '<br />'], "\n", $htmlBody));
    }

    $from = ngaged_mail_from();
    if (ngaged_smtp_config() !== null) {
        $result = ngaged_send_mail_smtp($to, $subject, $htmlBody, $textBody, $from);
        return $result['ok'];
    }

    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: text/html; charset=UTF-8',
        'From: ' . $from,
        'Reply-To: ' . $from,
    ];

    return @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $htmlBody, implode("\r\n", $headers));
}

/** @return array{ok:bool,transport:string,error?:string} */
function ngaged_send_mail_verbose(string $to, string $subject, string $htmlBody, string $textBody = ''): array
{
    if ($textBody === '') {
        $textBody = strip_tags(str_replace(['<br>', '<br/>', '<br />'], "\n", $htmlBody));
    }
    $from = ngaged_mail_from();
    if (ngaged_smtp_config() !== null) {
        $result = ngaged_send_mail_smtp($to, $subject, $htmlBody, $textBody, $from);
        return [
            'ok' => $result['ok'],
            'transport' => 'smtp',
            'error' => $result['error'] ?? null,
        ];
    }
    $ok = ngaged_send_mail($to, $subject, $htmlBody, $textBody);
    return ['ok' => $ok, 'transport' => ngaged_mail_transport_label(), 'error' => $ok ? null : 'mail() falló'];
}

function ngaged_campaign_email_html(array $campaign, array $member, string $approveUrl, string $declineUrl): string
{
    $preview = $campaign['preview'] ?? [];
    $title = htmlspecialchars((string) ($preview['title'] ?? $campaign['title'] ?? 'Nueva campaña'), ENT_QUOTES, 'UTF-8');
    $desc = htmlspecialchars((string) ($preview['description'] ?? ''), ENT_QUOTES, 'UTF-8');
    $image = htmlspecialchars((string) ($preview['image'] ?? ''), ENT_QUOTES, 'UTF-8');
    $name = htmlspecialchars((string) ($member['name'] ?? $member['email'] ?? ''), ENT_QUOTES, 'UTF-8');
    $commentary = htmlspecialchars((string) ($campaign['commentary'] ?? ''), ENT_QUOTES, 'UTF-8');

    $imgBlock = $image !== ''
        ? '<img src="' . $image . '" alt="" width="560" style="max-width:100%;border-radius:12px;margin:16px 0;" />'
        : '';

    return '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/></head><body style="margin:0;background:#eef3f8;font-family:Segoe UI,system-ui,sans-serif;color:#0b1929;">'
        . '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px;">'
        . '<table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;border:1px solid #d8e2ec;overflow:hidden;">'
        . '<tr><td style="padding:24px 28px;background:#0a66c2;color:#fff;"><strong style="font-size:18px;">Ngaged</strong><br/><span style="opacity:.9;font-size:14px;">Amplifica en LinkedIn con un clic</span></td></tr>'
        . '<tr><td style="padding:28px;"><p style="margin:0 0 8px;">Hola ' . $name . ',</p>'
        . '<p style="margin:0 0 16px;color:#5c6b7a;">Tu equipo te invita a repostear este contenido en LinkedIn.</p>'
        . $imgBlock
        . '<h2 style="margin:16px 0 8px;font-size:20px;">' . $title . '</h2>'
        . ($desc !== '' ? '<p style="margin:0 0 12px;color:#5c6b7a;">' . $desc . '</p>' : '')
        . ($commentary !== '' ? '<p style="margin:12px 0;padding:12px;background:#f7fafc;border-radius:8px;font-size:14px;"><strong>Tu comentario sugerido:</strong><br/>' . nl2br($commentary) . '</p>' : '')
        . '<table cellpadding="0" cellspacing="0" style="margin-top:24px;"><tr>'
        . '<td style="padding-right:12px;"><a href="' . htmlspecialchars($approveUrl, ENT_QUOTES) . '" style="display:inline-block;background:#0a66c2;color:#fff;text-decoration:none;padding:14px 22px;border-radius:10px;font-weight:600;">Repostear</a></td>'
        . '<td><a href="' . htmlspecialchars($declineUrl, ENT_QUOTES) . '" style="display:inline-block;background:#edf2f7;color:#0b1929;text-decoration:none;padding:14px 22px;border-radius:10px;font-weight:600;">Ignorar</a></td>'
        . '</tr></table>'
        . '<p style="margin:24px 0 0;font-size:12px;color:#94a3b8;">Si los botones no funcionan, abre el enlace desde el panel Ngaged.</p>'
        . '</td></tr></table></td></tr></table></body></html>';
}
