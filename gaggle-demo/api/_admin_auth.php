<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function ngaged_session_start(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
    session_name('NGAGEDSESSID');
    session_set_cookie_params([
        'lifetime' => 60 * 60 * 24 * 30,
        'path' => '/',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    $save = gaggle_demo_data_dir() . '/sessions';
    if (!is_dir($save)) {
        mkdir($save, 0700, true);
    }
    session_save_path($save);
    session_start();
}

/** @return array{admins:array<int,array<string,mixed>>} */
function ngaged_admins_store(): array
{
    $store = gaggle_demo_read_json_file('admins.json', ['admins' => []]);
    if (!isset($store['admins']) || !is_array($store['admins'])) {
        $store['admins'] = [];
    }
    return $store;
}

function ngaged_save_admins(array $store): void
{
    gaggle_demo_write_json_file('admins.json', $store);
}

function ngaged_bootstrap_admin_from_env(): void
{
    $store = ngaged_admins_store();
    if ($store['admins'] !== []) {
        return;
    }
    $env = gaggle_demo_load_env();
    $email = strtolower(trim($env['NGAGED_BOOTSTRAP_ADMIN_EMAIL'] ?? ''));
    $pass = (string) ($env['NGAGED_BOOTSTRAP_ADMIN_PASSWORD'] ?? '');
    if ($email === '' || $pass === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return;
    }
    $store['admins'][] = [
        'id' => gaggle_demo_new_id('adm'),
        'email' => $email,
        'name' => trim($env['NGAGED_BOOTSTRAP_ADMIN_NAME'] ?? '') ?: 'Administrador',
        'passwordHash' => password_hash($pass, PASSWORD_DEFAULT),
        'role' => 'admin',
        'active' => true,
        'createdAt' => gmdate('c'),
        'auth' => ['password' => true],
    ];
    ngaged_save_admins($store);
}

function ngaged_find_admin_by_email(array $store, string $email): ?array
{
    $email = strtolower(trim($email));
    foreach ($store['admins'] as $i => $a) {
        if (!is_array($a) || empty($a['active'])) {
            continue;
        }
        if (strtolower((string) ($a['email'] ?? '')) === $email) {
            return ['index' => $i, 'admin' => $a];
        }
    }
    return null;
}

function ngaged_find_admin_by_id(array $store, string $id): ?array
{
    foreach ($store['admins'] as $i => $a) {
        if (is_array($a) && ($a['id'] ?? '') === $id) {
            return ['index' => $i, 'admin' => $a];
        }
    }
    return null;
}

function ngaged_normalize_role(string $role): string
{
    $role = strtolower(trim($role));
    if ($role === 'owner') {
        return 'admin';
    }
    if ($role === 'manager') {
        return 'manager';
    }
    return 'admin';
}

function ngaged_admin_has_full_access(?array $admin): bool
{
    if ($admin === null) {
        return ngaged_legacy_admin_key_valid();
    }
    return ngaged_normalize_role((string) ($admin['role'] ?? 'admin')) === 'admin';
}

function ngaged_admin_public(array $admin): array
{
    $role = ngaged_normalize_role((string) ($admin['role'] ?? 'admin'));
    return [
        'id' => $admin['id'] ?? '',
        'email' => $admin['email'] ?? '',
        'name' => $admin['name'] ?? '',
        'role' => $role,
        'canManagePanelAccess' => $role === 'admin',
        'canManageMembers' => $role === 'admin',
    ];
}

function ngaged_login_admin(string $email, string $password): array
{
    require_once __DIR__ . '/_admin_2fa.php';
    $check = ngaged_verify_admin_password($email, $password);
    if (!$check['ok']) {
        return $check;
    }
    ngaged_establish_admin_session($check['admin']);
    return ['ok' => true, 'admin' => ngaged_admin_public($check['admin'])];
}

function ngaged_logout_admin(): void
{
    ngaged_session_start();
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', time() - 42000, $p['path'], $p['domain'] ?? '', $p['secure'], $p['httponly']);
    }
    session_destroy();
}

function ngaged_current_admin(): ?array
{
    ngaged_session_start();
    $id = (string) ($_SESSION['ngaged_admin_id'] ?? '');
    if ($id === '') {
        return null;
    }
    $found = ngaged_find_admin_by_id(ngaged_admins_store(), $id);
    if ($found === null || empty($found['admin']['active'])) {
        return null;
    }
    return $found['admin'];
}

function ngaged_legacy_admin_key_valid(): bool
{
    $expected = gaggle_demo_admin_key();
    if ($expected === '' || $expected === 'demo-admin') {
        return false;
    }
    $got = trim((string) ($_SERVER['HTTP_X_DEMO_ADMIN_KEY'] ?? ''));
    return $got !== '' && hash_equals($expected, $got);
}

function ngaged_require_admin_access(): void
{
    ngaged_bootstrap_admin_from_env();
    $admin = ngaged_current_admin();
    if ($admin !== null) {
        return;
    }
    if (ngaged_legacy_admin_key_valid()) {
        return;
    }
    gaggle_demo_json_response(401, [
        'ok' => false,
        'error' => 'Inicia sesión para continuar.',
        'loginRequired' => true,
    ]);
}

/** Cuenta con permiso completo (admin): gestionar accesos al panel y miembros. */
function ngaged_require_full_admin(): array
{
    ngaged_require_admin_access();
    $admin = ngaged_current_admin();
    if ($admin === null && ngaged_legacy_admin_key_valid()) {
        return ['id' => '', 'email' => '', 'name' => 'API', 'role' => 'admin', 'active' => true];
    }
    if ($admin === null) {
        gaggle_demo_json_response(403, ['ok' => false, 'error' => 'Sesión requerida.']);
    }
    if (!ngaged_admin_has_full_access($admin)) {
        gaggle_demo_json_response(403, ['ok' => false, 'error' => 'Solo un administrador con permiso completo puede hacer esto.']);
    }
    return $admin;
}

/** @deprecated use ngaged_require_full_admin */
function ngaged_require_owner(): array
{
    return ngaged_require_full_admin();
}

function ngaged_count_full_admins(array $store): int
{
    $n = 0;
    foreach ($store['admins'] ?? [] as $a) {
        if (is_array($a) && !empty($a['active']) && ngaged_admin_has_full_access($a)) {
            $n++;
        }
    }
    return $n;
}

function ngaged_google_oauth_configured(): bool
{
    $env = gaggle_demo_load_env();
    return trim($env['GOOGLE_CLIENT_ID'] ?? '') !== '' && trim($env['GOOGLE_CLIENT_SECRET'] ?? '') !== '';
}

function ngaged_app_url(): string
{
    $env = gaggle_demo_load_env();
    $url = trim($env['NGAGED_APP_URL'] ?? '');
    if ($url !== '') {
        return rtrim($url, '/');
    }
    $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    return $scheme . '://' . $host;
}
