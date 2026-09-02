<?php
/**
 * Sales Navigator customer accounts (password + email verification).
 */

declare(strict_types=1);

require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_unipile.php';

const CDE_CUSTOMER_PASSWORD_MIN = 8;
const CDE_CUSTOMER_VERIFY_HOURS = 48;

function cde_customers_file(): string
{
    return cde_salesnav_private_dir() . '/salesnav_customers.json';
}

function cde_customers_load(): array
{
    $path = cde_customers_file();
    if (!is_readable($path)) {
        return [];
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

function cde_customers_save(array $customers): void
{
    $path = cde_customers_file();
    @file_put_contents($path, json_encode($customers, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

function cde_customer_normalize_email(string $email): string
{
    return strtolower(trim($email));
}

function cde_customer_validate_email(string $email): ?string
{
    $email = cde_customer_normalize_email($email);
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return null;
    }
    return $email;
}

function cde_customer_validate_password(string $password): ?string
{
    $password = (string) $password;
    if (strlen($password) < CDE_CUSTOMER_PASSWORD_MIN) {
        return 'Password must be at least ' . CDE_CUSTOMER_PASSWORD_MIN . ' characters.';
    }
    return null;
}

function cde_customer_get_by_email(string $email): ?array
{
    $email = cde_customer_validate_email($email);
    if ($email === null) {
        return null;
    }
    $userId = cde_salesnav_user_id_for_email($email);
    $row = cde_customers_load()[$userId] ?? null;
    if (!is_array($row)) {
        return null;
    }
    $row['user_id'] = $userId;
    $row['email'] = $email;
    return $row;
}

function cde_customer_is_verified(string $email): bool
{
    $row = cde_customer_get_by_email($email);
    return is_array($row) && !empty($row['email_verified']);
}

function cde_customer_has_purchase_history(string $userId): bool
{
    require_once __DIR__ . '/_credits.php';
    if (cde_credits_get_balance($userId) > 0) {
        return true;
    }
    $path = cde_credits_ledger_file();
    if (!is_readable($path)) {
        return false;
    }
    $needleUser = '"user_id":"' . str_replace(['\\', '"'], ['\\\\', '\\"'], $userId) . '"';
    $handle = fopen($path, 'rb');
    if ($handle === false) {
        return false;
    }
    while (!feof($handle)) {
        $line = fgets($handle);
        if ($line === false) {
            break;
        }
        if (strpos($line, $needleUser) === false || strpos($line, 'stripe:') === false) {
            continue;
        }
        fclose($handle);
        return true;
    }
    fclose($handle);
    return false;
}

function cde_customer_site_origin(): string
{
    $cfg = function_exists('cde_unipile_read_env') ? cde_unipile_read_env() : [];
    $origin = trim((string) ($cfg['SALESNAV_SITE_ORIGIN'] ?? 'https://companydataenrichment.com'));
    return rtrim($origin, '/');
}

function cde_customer_send_verification_email(string $email, string $token): array
{
    $verifyUrl = cde_customer_site_origin() . '/salesnav/panel/?verify=' . rawurlencode($token);
    $subject = 'Confirm your CompanyDataEnrichment account';
    $body = implode("\n", [
        'Hi,',
        '',
        'Thanks for creating an account at CompanyDataEnrichment.',
        '',
        'Confirm your email address to activate your account:',
        $verifyUrl,
        '',
        'This link expires in ' . CDE_CUSTOMER_VERIFY_HOURS . ' hours.',
        '',
        'If you did not create this account, you can ignore this email.',
        '',
        '— CompanyDataEnrichment',
    ]);
    return cde_send_contact_mail($email, $subject, $body);
}

function cde_customer_issue_verify_token(string $userId): string
{
    $token = bin2hex(random_bytes(32));
    $customers = cde_customers_load();
    if (!isset($customers[$userId]) || !is_array($customers[$userId])) {
        $customers[$userId] = [];
    }
    $customers[$userId]['verify_token_hash'] = hash('sha256', $token);
    $customers[$userId]['verify_expires'] = gmdate('c', time() + CDE_CUSTOMER_VERIFY_HOURS * 3600);
    cde_customers_save($customers);
    return $token;
}

function cde_customer_mark_verified(string $userId): void
{
    $customers = cde_customers_load();
    if (!isset($customers[$userId]) || !is_array($customers[$userId])) {
        return;
    }
    $customers[$userId]['email_verified'] = true;
    $customers[$userId]['verified_at'] = gmdate('c');
    unset($customers[$userId]['verify_token_hash'], $customers[$userId]['verify_expires']);
    cde_customers_save($customers);
}

/**
 * @return array{ok: bool, email?: string, user_id?: string, needs_verification?: bool, error?: string, code?: string}
 */
function cde_customer_register(string $email, string $password, string $passwordConfirm): array
{
    $email = cde_customer_validate_email($email);
    if ($email === null) {
        return ['ok' => false, 'code' => 'invalid_email', 'error' => 'Invalid email address.'];
    }
    if ($pwErr = cde_customer_validate_password($password)) {
        return ['ok' => false, 'code' => 'weak_password', 'error' => $pwErr];
    }
    if ($password !== $passwordConfirm) {
        return ['ok' => false, 'code' => 'password_mismatch', 'error' => 'Passwords do not match.'];
    }

    $ip = cde_client_ip();
    $rate = cde_rate_consume('salesnav_register_ip_hour', $ip, 8, 3600);
    if (!$rate['ok']) {
        return ['ok' => false, 'code' => 'rate_limited', 'error' => 'Too many sign-up attempts. Try again later.'];
    }

    $userId = cde_salesnav_user_id_for_email($email);
    $customers = cde_customers_load();
    $existing = $customers[$userId] ?? null;
    if (is_array($existing) && !empty($existing['email_verified'])) {
        return ['ok' => false, 'code' => 'email_exists', 'error' => 'An account with this email already exists. Sign in instead.'];
    }

    $autoVerify = cde_customer_has_purchase_history($userId);
    $hash = password_hash($password, PASSWORD_DEFAULT);
    $now = gmdate('c');

    $customers[$userId] = [
        'email' => $email,
        'password_hash' => $hash,
        'email_verified' => $autoVerify,
        'created_at' => is_array($existing) ? ($existing['created_at'] ?? $now) : $now,
        'verified_at' => $autoVerify ? ($existing['verified_at'] ?? $now) : null,
    ];
    cde_customers_save($customers);

    if ($autoVerify) {
        return [
            'ok' => true,
            'email' => $email,
            'user_id' => $userId,
            'needs_verification' => false,
        ];
    }

    $token = cde_customer_issue_verify_token($userId);
    $mail = cde_customer_send_verification_email($email, $token);
    if (!$mail['ok']) {
        return ['ok' => false, 'code' => 'mail_failed', 'error' => 'Could not send verification email. Try again later.'];
    }

    return [
        'ok' => true,
        'email' => $email,
        'user_id' => $userId,
        'needs_verification' => true,
    ];
}

/**
 * @return array{ok: bool, email?: string, user_id?: string, balance?: int, error?: string, code?: string}
 */
function cde_customer_sign_in(string $email, string $password): array
{
    $email = cde_customer_validate_email($email);
    if ($email === null) {
        return ['ok' => false, 'code' => 'invalid_email', 'error' => 'Invalid email address.'];
    }
    if ($password === '') {
        return ['ok' => false, 'code' => 'missing_password', 'error' => 'Password is required.'];
    }

    $ip = cde_client_ip();
    $rate = cde_rate_consume('salesnav_signin_' . hash('sha256', $email), $ip, 12, 900);
    if (!$rate['ok']) {
        return ['ok' => false, 'code' => 'rate_limited', 'error' => 'Too many sign-in attempts. Try again later.'];
    }

    $row = cde_customer_get_by_email($email);
    if (!is_array($row) || empty($row['password_hash']) || !is_string($row['password_hash'])) {
        return ['ok' => false, 'code' => 'invalid_credentials', 'error' => 'Invalid email or password.'];
    }
    if (!password_verify($password, $row['password_hash'])) {
        return ['ok' => false, 'code' => 'invalid_credentials', 'error' => 'Invalid email or password.'];
    }
    if (empty($row['email_verified'])) {
        return ['ok' => false, 'code' => 'needs_verification', 'error' => 'Confirm your email before signing in. Check your inbox or resend the confirmation email.'];
    }

    $userId = cde_salesnav_login_customer($email);
    require_once __DIR__ . '/_credits.php';
    $balance = cde_credits_get_balance($userId);

    return [
        'ok' => true,
        'email' => $email,
        'user_id' => $userId,
        'balance' => $balance,
    ];
}

/**
 * @return array{ok: bool, error?: string, code?: string}
 */
function cde_customer_resend_verification(string $email): array
{
    $email = cde_customer_validate_email($email);
    if ($email === null) {
        return ['ok' => false, 'code' => 'invalid_email', 'error' => 'Invalid email address.'];
    }

    $ip = cde_client_ip();
    $rate = cde_rate_consume('salesnav_resend_' . hash('sha256', $email), $ip, 4, 3600);
    if (!$rate['ok']) {
        return ['ok' => false, 'code' => 'rate_limited', 'error' => 'Too many requests. Try again later.'];
    }

    $row = cde_customer_get_by_email($email);
    if (!is_array($row)) {
        return ['ok' => true];
    }
    if (!empty($row['email_verified'])) {
        return ['ok' => true];
    }

    $userId = (string) $row['user_id'];
    $token = cde_customer_issue_verify_token($userId);
    $mail = cde_customer_send_verification_email($email, $token);
    if (!$mail['ok']) {
        return ['ok' => false, 'code' => 'mail_failed', 'error' => 'Could not send verification email. Try again later.'];
    }

    return ['ok' => true];
}

/**
 * @return array{ok: bool, email?: string, user_id?: string, balance?: int, error?: string, code?: string}
 */
function cde_customer_verify_token(string $token): array
{
    $token = trim($token);
    if ($token === '' || !preg_match('/^[a-f0-9]{64}$/i', $token)) {
        return ['ok' => false, 'code' => 'invalid_token', 'error' => 'Invalid or expired confirmation link.'];
    }

    $hash = hash('sha256', $token);
    $customers = cde_customers_load();
    $matchUserId = null;
    $matchEmail = null;
    $now = time();

    foreach ($customers as $userId => $row) {
        if (!is_array($row)) {
            continue;
        }
        if (($row['verify_token_hash'] ?? '') !== $hash) {
            continue;
        }
        $expires = strtotime((string) ($row['verify_expires'] ?? ''));
        if ($expires === false || $expires < $now) {
            return ['ok' => false, 'code' => 'expired_token', 'error' => 'This confirmation link has expired. Request a new one.'];
        }
        $matchUserId = (string) $userId;
        $matchEmail = cde_customer_normalize_email((string) ($row['email'] ?? ''));
        break;
    }

    if ($matchUserId === null || $matchEmail === null || $matchEmail === '') {
        return ['ok' => false, 'code' => 'invalid_token', 'error' => 'Invalid or expired confirmation link.'];
    }

    cde_customer_mark_verified($matchUserId);
    $loggedUserId = cde_salesnav_login_customer($matchEmail);
    require_once __DIR__ . '/_credits.php';
    $balance = cde_credits_get_balance($loggedUserId);

    return [
        'ok' => true,
        'email' => $matchEmail,
        'user_id' => $loggedUserId,
        'balance' => $balance,
    ];
}

function cde_salesnav_session_is_authenticated(): bool
{
    cde_session_start();
    if (empty($_SESSION['salesnav_auth_ok'])) {
        return false;
    }
    $email = cde_customer_normalize_email((string) ($_SESSION['salesnav_customer_email'] ?? ''));
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return false;
    }
    return cde_customer_is_verified($email);
}

function cde_salesnav_establish_session(string $email): void
{
    $email = cde_customer_normalize_email($email);
    cde_session_start();
    $prevId = cde_salesnav_anonymous_user_id();
    $_SESSION['salesnav_customer_email'] = $email;
    $_SESSION['salesnav_auth_ok'] = true;
    $_SESSION['salesnav_auth_at'] = gmdate('c');
    session_regenerate_id(true);
    $nextId = cde_salesnav_user_id_for_email($email);
    if ($prevId !== $nextId && function_exists('cde_credits_merge_wallets')) {
        cde_credits_merge_wallets($prevId, $nextId);
    }
}

/** Anonymous browser wallet id (before email login). */
function cde_salesnav_anonymous_user_id(): string
{
    cde_session_start();
    if (!empty($_SESSION['salesnav_auth_ok'])) {
        $email = cde_customer_normalize_email((string) ($_SESSION['salesnav_customer_email'] ?? ''));
        if ($email !== '' && filter_var($email, FILTER_VALIDATE_EMAIL) && cde_customer_is_verified($email)) {
            return cde_salesnav_user_id_for_email($email);
        }
    }
    if (empty($_SESSION['salesnav_user_id']) || !is_string($_SESSION['salesnav_user_id'])) {
        $_SESSION['salesnav_user_id'] = bin2hex(random_bytes(16));
    }
    return (string) $_SESSION['salesnav_user_id'];
}

function cde_salesnav_login_customer(string $email): string
{
    $email = cde_customer_validate_email($email);
    if ($email === null) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid email address.']);
    }
    cde_salesnav_establish_session($email);
    return cde_salesnav_user_id_for_email($email);
}

/**
 * @return array{email: string, user_id: string}
 */
function cde_salesnav_require_auth(): array
{
    if (!cde_salesnav_session_is_authenticated()) {
        cde_json_response(401, [
            'ok' => false,
            'needs_auth' => true,
            'error' => 'Sign in to continue.',
        ]);
    }
    $email = cde_customer_normalize_email((string) ($_SESSION['salesnav_customer_email'] ?? ''));
    return [
        'email' => $email,
        'user_id' => cde_salesnav_user_id_for_email($email),
    ];
}
