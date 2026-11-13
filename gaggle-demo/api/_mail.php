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

/**
 * @param array{like:string,repost:string,like_repost:string,decline:string} $urls
 */
function ngaged_campaign_email_html(array $campaign, array $member, array $urls): string
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
        . '<p style="margin:0 0 16px;color:#5c6b7a;">Tu equipo te invita a amplificar este post en LinkedIn. Elige una opción (un clic cada una).</p>'
        . $imgBlock
        . '<h2 style="margin:16px 0 8px;font-size:20px;">' . $title . '</h2>'
        . ($desc !== '' ? '<p style="margin:0 0 12px;color:#5c6b7a;">' . $desc . '</p>' : '')
        . ($commentary !== '' ? '<p style="margin:12px 0;padding:12px;background:#f7fafc;border-radius:8px;font-size:14px;"><strong>Tu comentario sugerido:</strong><br/>' . nl2br($commentary) . '</p>' : '')
        . '<table cellpadding="0" cellspacing="0" style="margin-top:24px;width:100%;"><tr>'
        . '<td style="padding:0 8px 10px 0;width:50%;"><a href="' . htmlspecialchars($urls['like_repost'], ENT_QUOTES) . '" style="display:block;text-align:center;background:#0a66c2;color:#fff;text-decoration:none;padding:14px 16px;border-radius:10px;font-weight:600;">Me gusta + Repost</a></td>'
        . '<td style="padding:0 0 10px 8px;width:50%;"><a href="' . htmlspecialchars($urls['repost'], ENT_QUOTES) . '" style="display:block;text-align:center;background:#1b4f8a;color:#fff;text-decoration:none;padding:14px 16px;border-radius:10px;font-weight:600;">Solo repost</a></td>'
        . '</tr><tr>'
        . '<td style="padding:0 8px 0 0;width:50%;"><a href="' . htmlspecialchars($urls['like'], ENT_QUOTES) . '" style="display:block;text-align:center;background:#edf2f7;color:#0b1929;text-decoration:none;padding:12px 16px;border-radius:10px;font-weight:600;">Solo me gusta</a></td>'
        . '<td style="padding:0 0 0 8px;width:50%;"><a href="' . htmlspecialchars($urls['decline'], ENT_QUOTES) . '" style="display:block;text-align:center;background:#f8fafc;color:#64748b;text-decoration:none;padding:12px 16px;border-radius:10px;font-weight:600;border:1px solid #e2e8f0;">Ignorar</a></td>'
        . '</tr></table>'
        . '<p style="margin:16px 0 0;font-size:11px;color:#94a3b8;">«Me gusta + Repost» aplica ambas acciones en LinkedIn con un breve intervalo entre ellas.</p>'
        . '<p style="margin:24px 0 0;font-size:12px;color:#94a3b8;">Si los botones no funcionan, abre el enlace desde el panel Ngaged.</p>'
        . '</td></tr></table></td></tr></table></body></html>';
}

function ngaged_connect_invite_email_subject(): string
{
    return 'Invitación a Ngaged — vincula tu LinkedIn';
}

function ngaged_connect_invite_email_text(string $name, string $inviteUrl): string
{
    $who = $name !== '' ? $name : 'Hola';
    return "{$who},\n\n"
        . "Tu organización usa Ngaged para campañas de employee advocacy en LinkedIn: "
        . "recibirás propuestas de contenido y podrás responder con un clic (me gusta, repost o ambos).\n\n"
        . "El primer paso es vincular tu perfil de LinkedIn (solo una vez):\n{$inviteUrl}\n\n"
        . "Cuando completes la vinculación, un administrador validará tu alta y te asignará un equipo.\n\n"
        . "— Ngaged\n";
}

function ngaged_connect_invite_email_html(string $name, string $inviteUrl): string
{
    $name = htmlspecialchars($name !== '' ? $name : 'Hola', ENT_QUOTES, 'UTF-8');
    $url = htmlspecialchars($inviteUrl, ENT_QUOTES, 'UTF-8');

    return '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/></head><body style="margin:0;background:#eef3f8;font-family:Segoe UI,system-ui,sans-serif;color:#0b1929;">'
        . '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px;">'
        . '<table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;border:1px solid #d8e2ec;overflow:hidden;">'
        . '<tr><td style="padding:24px 28px;background:#0a66c2;color:#fff;"><strong style="font-size:18px;">Ngaged</strong>'
        . '<br/><span style="opacity:.9;font-size:14px;">Employee advocacy en LinkedIn</span></td></tr>'
        . '<tr><td style="padding:28px;">'
        . '<p style="margin:0 0 8px;">Hola ' . $name . ',</p>'
        . '<p style="margin:0 0 16px;color:#5c6b7a;">Tu equipo ha activado <strong>Ngaged</strong> para amplificar la marca en LinkedIn de forma voluntaria y con un solo clic.</p>'
        . '<p style="margin:0 0 12px;color:#5c6b7a;font-size:14px;">Ngaged te enviará por email campañas puntuales; tú eliges si das me gusta, republicas o ignoras. No tienes que copiar textos ni entrar en paneles complicados.</p>'
        . '<p style="margin:0 0 20px;color:#5c6b7a;font-size:14px;"><strong>Primer paso:</strong> vincula tu cuenta de LinkedIn (solo una vez, menos de un minuto). Después, un administrador validará tu alta y te asignará un equipo.</p>'
        . '<a href="' . $url . '" style="display:block;text-align:center;background:#0a66c2;color:#fff;text-decoration:none;padding:16px 20px;border-radius:10px;font-weight:600;margin:0 0 16px;">Vincular mi LinkedIn con Ngaged</a>'
        . '<p style="margin:0;font-size:12px;color:#94a3b8;">Si el botón no funciona, copia este enlace en el navegador:<br/><span style="word-break:break-all;">' . $url . '</span></p>'
        . '</td></tr></table></td></tr></table></body></html>';
}
