<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';
require_once __DIR__ . '/_mail.php';

function ngaged_admin_2fa_enabled(): bool
{
    $env = gaggle_demo_load_env();
    $v = strtolower(trim($env['NGAGED_ADMIN_2FA'] ?? '1'));
    return !in_array($v, ['0', 'false', 'no', 'off'], true);
}

/** @return array{challenges:array<int,array<string,mixed>>} */
function ngaged_login_challenges_store(): array
{
    $store = gaggle_demo_read_json_file('login_challenges.json', ['challenges' => []]);
    if (!isset($store['challenges']) || !is_array($store['challenges'])) {
        $store['challenges'] = [];
    }
    return $store;
}

function ngaged_save_login_challenges(array $store): void
{
    gaggle_demo_write_json_file('login_challenges.json', $store);
}

function ngaged_purge_expired_challenges(array $store): array
{
    $now = time();
    $store['challenges'] = array_values(array_filter(
        $store['challenges'],
        static fn ($c) => is_array($c) && strtotime((string) ($c['expiresAt'] ?? '')) > $now
    ));
    return $store;
}

function ngaged_verify_admin_password(string $email, string $password): array
{
    ngaged_bootstrap_admin_from_env();
    $store = ngaged_admins_store();
    $found = ngaged_find_admin_by_email($store, $email);
    if ($found === null) {
        return ['ok' => false, 'error' => 'Email o contraseña incorrectos.'];
    }
    $admin = $found['admin'];
    $hash = (string) ($admin['passwordHash'] ?? '');
    if ($hash === '' || !password_verify($password, $hash)) {
        return ['ok' => false, 'error' => 'Email o contraseña incorrectos.'];
    }
    return ['ok' => true, 'admin' => $admin];
}

function ngaged_establish_admin_session(array $admin): void
{
    ngaged_session_start();
    session_regenerate_id(true);
    $_SESSION['ngaged_admin_id'] = $admin['id'];
    $_SESSION['ngaged_admin_email'] = $admin['email'];
}

function ngaged_login_2fa_email_subject(): string
{
    return 'Tu acceso a Ngaged — código de verificación';
}

function ngaged_login_2fa_email_text(string $name, string $code, int $minutes): string
{
    $who = $name !== '' ? $name : 'Administrador';
    return "Hola {$who},\n\n"
        . "Tu código de verificación para entrar en Ngaged es: {$code}\n\n"
        . "Caduca en {$minutes} minutos.\n\n"
        . "Si no has solicitado este acceso, ignora este mensaje.\n\n"
        . "— Ngaged\n";
}

function ngaged_login_2fa_email_html(string $name, string $code, int $minutes): string
{
    $name = htmlspecialchars($name !== '' ? $name : 'Administrador', ENT_QUOTES, 'UTF-8');
    $code = htmlspecialchars($code, ENT_QUOTES, 'UTF-8');
    $appUrl = htmlspecialchars(ngaged_app_base_url(), ENT_QUOTES, 'UTF-8');
    return '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/></head><body style="margin:0;background:#eef3f8;font-family:Segoe UI,system-ui,sans-serif;color:#0b1929;">'
        . '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px;">'
        . '<table width="480" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;border:1px solid #d8e2ec;overflow:hidden;">'
        . '<tr><td style="padding:20px 24px;background:#0a66c2;color:#fff;"><strong style="font-size:17px;">Ngaged</strong>'
        . '<br/><span style="opacity:.9;font-size:13px;">Verificación de acceso al panel</span></td></tr>'
        . '<tr><td style="padding:24px 28px;">'
        . '<p style="margin:0 0 12px;">Hola ' . $name . ',</p>'
        . '<p style="margin:0 0 16px;color:#5c6b7a;">Introduce este código en la pantalla de login:</p>'
        . '<p style="font-size:32px;font-weight:700;letter-spacing:8px;margin:20px 0;text-align:center;color:#0b1929;">' . $code . '</p>'
        . '<p style="margin:0 0 8px;color:#5c6b7a;font-size:14px;">Caduca en ' . (int) $minutes . ' minutos.</p>'
        . '<p style="margin:16px 0 0;font-size:12px;color:#94a3b8;">Si no has sido tú, ignora este mensaje. '
        . ($appUrl !== '' ? 'Panel: <a href="' . $appUrl . '/login" style="color:#0a66c2;">' . $appUrl . '/login</a>' : '')
        . '</p></td></tr></table></td></tr></table></body></html>';
}

/** @return array{ok:bool,loginToken?:string,emailMasked?:string,error?:string} */
function ngaged_start_login_2fa(array $admin): array
{
    $email = (string) ($admin['email'] ?? '');
    if ($email === '') {
        return ['ok' => false, 'error' => 'Cuenta inválida.'];
    }

    $store = ngaged_purge_expired_challenges(ngaged_login_challenges_store());
    $recent = 0;
    $since = time() - 900;
    foreach ($store['challenges'] as $c) {
        if (is_array($c) && ($c['email'] ?? '') === $email && strtotime((string) ($c['createdAt'] ?? '')) >= $since) {
            $recent++;
        }
    }
    if ($recent >= 5) {
        return ['ok' => false, 'error' => 'Demasiados intentos. Espera unos minutos e inténtalo de nuevo.'];
    }

    $code = (string) random_int(100000, 999999);
    $token = bin2hex(random_bytes(16));
    $ttlMin = 10;
    $store['challenges'][] = [
        'token' => $token,
        'adminId' => $admin['id'] ?? '',
        'email' => $email,
        'codeHash' => password_hash($code, PASSWORD_DEFAULT),
        'attempts' => 0,
        'createdAt' => gmdate('c'),
        'expiresAt' => gmdate('c', time() + ($ttlMin * 60)),
    ];
    ngaged_save_login_challenges($store);

    $subject = ngaged_login_2fa_email_subject();
    $adminName = (string) ($admin['name'] ?? '');
    $html = ngaged_login_2fa_email_html($adminName, $code, $ttlMin);
    $text = ngaged_login_2fa_email_text($adminName, $code, $ttlMin);
    $sentResult = ngaged_send_mail_verbose($email, $subject, $html, $text);
    if (!$sentResult['ok']) {
        $hint = $sentResult['error'] ?? 'Revisa SMTP en el servidor.';
        return ['ok' => false, 'error' => 'No pudimos enviar el email de verificación. ' . $hint];
    }

    $parts = explode('@', $email);
    $masked = substr($parts[0], 0, 1) . '***@' . ($parts[1] ?? '');

    return ['ok' => true, 'loginToken' => $token, 'emailMasked' => $masked];
}

/** @return array{ok:bool,admin?:array,error?:string} */
function ngaged_complete_login_2fa(string $loginToken, string $code): array
{
    $loginToken = trim($loginToken);
    $code = preg_replace('/\D/', '', $code) ?? '';
    if ($loginToken === '' || strlen($code) !== 6) {
        return ['ok' => false, 'error' => 'Código inválido.'];
    }

    $store = ngaged_purge_expired_challenges(ngaged_login_challenges_store());
    $idx = null;
    foreach ($store['challenges'] as $i => $c) {
        if (is_array($c) && hash_equals((string) ($c['token'] ?? ''), $loginToken)) {
            $idx = $i;
            break;
        }
    }
    if ($idx === null) {
        return ['ok' => false, 'error' => 'El código ha caducado. Vuelve a iniciar sesión.'];
    }

    $row = $store['challenges'][$idx];
    $attempts = (int) ($row['attempts'] ?? 0) + 1;
    $store['challenges'][$idx]['attempts'] = $attempts;
    ngaged_save_login_challenges($store);

    if ($attempts > 5) {
        unset($store['challenges'][$idx]);
        $store['challenges'] = array_values($store['challenges']);
        ngaged_save_login_challenges($store);
        return ['ok' => false, 'error' => 'Demasiados intentos. Vuelve a iniciar sesión.'];
    }

    if (!password_verify($code, (string) ($row['codeHash'] ?? ''))) {
        return ['ok' => false, 'error' => 'Código incorrecto.'];
    }

    $found = ngaged_find_admin_by_id(ngaged_admins_store(), (string) ($row['adminId'] ?? ''));
    if ($found === null || empty($found['admin']['active'])) {
        return ['ok' => false, 'error' => 'Cuenta no disponible.'];
    }

    unset($store['challenges'][$idx]);
    $store['challenges'] = array_values($store['challenges']);
    ngaged_save_login_challenges($store);

    $admin = $found['admin'];
    ngaged_establish_admin_session($admin);
    return ['ok' => true, 'admin' => ngaged_admin_public($admin)];
}
