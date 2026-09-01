<?php
/**
 * Unipile helpers for Sales Navigator export (NavExport simple tier).
 */

declare(strict_types=1);

function cde_unipile_env_paths(): array
{
    return [
        dirname(__DIR__, 2) . '/private/cde/unipile.env',
        __DIR__ . '/unipile.env',
    ];
}

function cde_unipile_read_env(): array
{
    $env = [];
    foreach (cde_unipile_env_paths() as $path) {
        if (!is_readable($path)) {
            continue;
        }
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $env[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }
    return $env;
}

function cde_unipile_api_config(?string $accountId = null): array
{
    $env = cde_unipile_read_env();
    $apiKey = $env['UNIPILE_API_KEY'] ?? getenv('UNIPILE_API_KEY') ?: '';
    $base = $env['UNIPILE_BASE_URL'] ?? getenv('UNIPILE_BASE_URL') ?: 'https://api.unipile.com/v2';
    $base = rtrim(trim($base), '/');

    if ($apiKey === '') {
        cde_json_response(500, [
            'ok' => false,
            'error' => 'Server misconfigured: Unipile API key missing.',
        ]);
    }

    $isV1 = (strpos($base, '/api/v1') !== false)
        || (substr($base, -3) !== '/v2' && strpos($base, 'api.unipile.com/v2') === false);

    $resolvedAccount = $accountId
        ?? ($env['UNIPILE_ACCOUNT_ID'] ?? getenv('UNIPILE_ACCOUNT_ID') ?: '');

    return [
        'api_key' => $apiKey,
        'account_id' => $resolvedAccount,
        'base' => $base,
        'is_v1' => $isV1,
        'dsn_url' => cde_unipile_dsn_url($base),
        'notify_secret' => (string) ($env['SALESNAV_NOTIFY_SECRET'] ?? ''),
        'site_origin' => (string) ($env['SALESNAV_SITE_ORIGIN'] ?? 'https://companydataenrichment.com'),
        'hosted_auth_domain' => cde_salesnav_normalize_hosted_auth_domain(
            (string) ($env['SALESNAV_HOSTED_AUTH_DOMAIN'] ?? getenv('SALESNAV_HOSTED_AUTH_DOMAIN') ?: '')
        ),
    ];
}

/** @deprecated use cde_unipile_api_config() */
function cde_load_unipile_config(): array
{
    return cde_unipile_api_config();
}

function cde_unipile_dsn_url(string $apiBase): string
{
    $base = rtrim($apiBase, '/');
    if (preg_match('#^(https?://[^/]+(?::\d+)?)/api/v\d+$#', $base, $m)) {
        return $m[1];
    }
    if (substr($base, -3) === '/v2') {
        return substr($base, 0, -3);
    }
    return $base;
}

/** Hostname only, no scheme or path (e.g. connect.companydataenrichment.com). */
function cde_salesnav_normalize_hosted_auth_domain(string $value): string
{
    $value = trim($value);
    if ($value === '') {
        return '';
    }
    $value = preg_replace('#^https?://#i', '', $value) ?? $value;
    $value = rtrim($value, '/');
    if (!preg_match('/^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/i', $value)) {
        return '';
    }
    return strtolower($value);
}

/** True when the white-label host is publicly resolvable (CNAME or A). */
function cde_salesnav_hosted_auth_domain_resolves(string $domain): bool
{
    $domain = cde_salesnav_normalize_hosted_auth_domain($domain);
    if ($domain === '') {
        return false;
    }

    $records = @dns_get_record($domain, DNS_CNAME | DNS_A);
    return is_array($records) && $records !== [];
}

/** True when HTTPS presents a valid cert for the custom domain (Unipile white-label ready). */
function cde_salesnav_hosted_auth_domain_ssl_ready(string $domain): bool
{
    $domain = cde_salesnav_normalize_hosted_auth_domain($domain);
    if ($domain === '') {
        return false;
    }

    $ctx = stream_context_create([
        'ssl' => [
            'verify_peer' => true,
            'verify_peer_name' => true,
            'peer_name' => $domain,
            'SNI_enabled' => true,
        ],
    ]);

    $fp = @stream_socket_client(
        'ssl://' . $domain . ':443',
        $errno,
        $errstr,
        8,
        STREAM_CLIENT_CONNECT,
        $ctx
    );

    if ($fp === false) {
        return false;
    }

    fclose($fp);
    return true;
}

/**
 * Apply white-label rewrite only when DNS and Unipile SSL for the domain are ready.
 * Falls back to account.unipile.com until Piensa DNS + Unipile Hosted Auth validation complete.
 */
function cde_salesnav_apply_hosted_auth_domain(string $url, string $domain): string
{
    $domain = cde_salesnav_normalize_hosted_auth_domain($domain);
    if ($domain === ''
        || !cde_salesnav_hosted_auth_domain_resolves($domain)
        || !cde_salesnav_hosted_auth_domain_ssl_ready($domain)) {
        return $url;
    }
    return cde_salesnav_rewrite_hosted_auth_url($url, $domain);
}

/**
 * Replace Unipile hosted-auth host with our white-label subdomain.
 * @see https://developer.unipile.com/docs/hosted-auth#custom-domain-url-white-label
 */
function cde_salesnav_rewrite_hosted_auth_url(string $url, ?string $domain = null): string
{
    $domain = cde_salesnav_normalize_hosted_auth_domain($domain ?? '');
    if ($domain === '' || $url === '') {
        return $url;
    }

    $parts = parse_url($url);
    if (!is_array($parts) || empty($parts['host'])) {
        return $url;
    }

    $host = strtolower((string) $parts['host']);
    $unipileHosts = ['account.unipile.com', 'auth.unipile.com'];
    if (!in_array($host, $unipileHosts, true)) {
        return $url;
    }

    $parts['scheme'] = 'https';
    $parts['host'] = $domain;

    $rewritten = cde_salesnav_build_url($parts);
    return $rewritten !== '' ? $rewritten : $url;
}

function cde_salesnav_build_url(array $parts): string
{
    $scheme = isset($parts['scheme']) ? $parts['scheme'] . '://' : '';
    $host = (string) ($parts['host'] ?? '');
    if ($host === '') {
        return '';
    }

    $port = isset($parts['port']) ? ':' . $parts['port'] : '';
    $user = (string) ($parts['user'] ?? '');
    $pass = isset($parts['pass']) ? ':' . $parts['pass'] : '';
    $auth = $user !== '' ? $user . $pass . '@' : '';
    $path = (string) ($parts['path'] ?? '');
    $query = isset($parts['query']) ? '?' . $parts['query'] : '';
    $fragment = isset($parts['fragment']) ? '#' . $parts['fragment'] : '';

    return $scheme . $auth . $host . $port . $path . $query . $fragment;
}

function cde_salesnav_private_dir(): string
{
    $dir = dirname(__DIR__, 2) . '/private/cde';
    if (!is_dir($dir)) {
        @mkdir($dir, 0700, true);
    }
    return $dir;
}

function cde_salesnav_accounts_file(): string
{
    return cde_salesnav_private_dir() . '/salesnav_accounts.json';
}

function cde_salesnav_user_id(): string
{
    cde_session_start();
    if (!empty($_SESSION['salesnav_auth_ok'])) {
        $email = strtolower(trim((string) ($_SESSION['salesnav_customer_email'] ?? '')));
        if ($email !== '' && filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $verifiedOk = true;
            if (function_exists('cde_customer_is_verified')) {
                $verifiedOk = cde_customer_is_verified($email);
            }
            if ($verifiedOk) {
                return cde_salesnav_user_id_for_email($email);
            }
        }
    }
    if (function_exists('cde_salesnav_anonymous_user_id')) {
        return cde_salesnav_anonymous_user_id();
    }
    if (empty($_SESSION['salesnav_user_id']) || !is_string($_SESSION['salesnav_user_id'])) {
        $_SESSION['salesnav_user_id'] = bin2hex(random_bytes(16));
    }
    return (string) $_SESSION['salesnav_user_id'];
}

function cde_salesnav_session_email(): ?string
{
    if (function_exists('cde_salesnav_session_is_authenticated') && !cde_salesnav_session_is_authenticated()) {
        return null;
    }
    cde_session_start();
    $email = strtolower(trim((string) ($_SESSION['salesnav_customer_email'] ?? '')));
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return null;
    }
    return $email;
}

function cde_salesnav_user_id_for_email(string $email): string
{
    $email = strtolower(trim($email));
    return 'em_' . hash('sha256', $email);
}

/** @deprecated Use password login via salesnav-account.php */
function cde_salesnav_bind_customer_email(string $email): string
{
    $email = strtolower(trim($email));
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid email address.']);
    }
    if (function_exists('cde_customer_is_verified') && cde_customer_is_verified($email)) {
        return cde_salesnav_login_customer($email);
    }
    cde_session_start();
    $prevId = cde_salesnav_user_id();
    $nextId = cde_salesnav_user_id_for_email($email);
    if ($prevId !== $nextId && function_exists('cde_credits_merge_wallets')) {
        cde_credits_merge_wallets($prevId, $nextId);
    }
    return $nextId;
}

function cde_salesnav_sign_out_customer(): void
{
    cde_session_start();
    unset(
        $_SESSION['salesnav_customer_email'],
        $_SESSION['salesnav_auth_ok'],
        $_SESSION['salesnav_auth_at']
    );
}

function cde_salesnav_load_accounts(): array
{
    $path = cde_salesnav_accounts_file();
    if (!is_readable($path)) {
        return [];
    }
    $raw = file_get_contents($path);
    $data = json_decode((string) $raw, true);
    return is_array($data) ? $data : [];
}

function cde_salesnav_save_account(string $userId, array $record): void
{
    $all = cde_salesnav_load_accounts();
    $all[$userId] = $record;
    $path = cde_salesnav_accounts_file();
    @file_put_contents($path, json_encode($all, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

/** Persisted LinkedIn link for a wallet (survives panel disconnect). */
function cde_salesnav_stored_account(?string $userId = null): ?array
{
    $userId = $userId ?? cde_salesnav_user_id();
    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    if (!is_array($stored) || empty($stored['account_id'])) {
        return null;
    }
    return $stored;
}

/** Stored account eligible for reconnect (kept after disconnect). */
function cde_salesnav_reconnect_account(?string $userId = null): ?array
{
    $stored = cde_salesnav_stored_account($userId);
    if ($stored === null) {
        return null;
    }
    return $stored;
}

/** Copy LinkedIn connection from an anonymous wallet to the email-based wallet on login. */
function cde_salesnav_merge_accounts(string $fromUserId, string $toUserId): void
{
    if ($fromUserId === '' || $toUserId === '' || $fromUserId === $toUserId) {
        return;
    }
    $all = cde_salesnav_load_accounts();
    $from = $all[$fromUserId] ?? null;
    $to = $all[$toUserId] ?? null;
    if (!is_array($from) || empty($from['account_id'])) {
        return;
    }
    if (is_array($to) && !empty($to['account_id'])) {
        return;
    }
    $all[$toUserId] = array_merge($from, [
        'linked_at' => (string) ($from['linked_at'] ?? gmdate('c')),
    ]);
    $path = cde_salesnav_accounts_file();
    @file_put_contents($path, json_encode($all, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

function cde_salesnav_set_session_account(string $accountId, string $label = '', string $avatarUrl = ''): void
{
    cde_session_start();
    $_SESSION['salesnav_account_id'] = $accountId;
    $_SESSION['salesnav_account_label'] = $label;
    $_SESSION['salesnav_account_avatar'] = $avatarUrl;
    $_SESSION['salesnav_connected_at'] = gmdate('c');
}

function cde_salesnav_clear_session_account(): void
{
    cde_session_start();
    unset(
        $_SESSION['salesnav_account_id'],
        $_SESSION['salesnav_account_label'],
        $_SESSION['salesnav_account_avatar'],
        $_SESSION['salesnav_connected_at']
    );
}

function cde_salesnav_session_account(): ?array
{
    cde_session_start();
    $accountId = trim((string) ($_SESSION['salesnav_account_id'] ?? ''));
    if ($accountId === '') {
        $userId = cde_salesnav_user_id();
        $stored = cde_salesnav_load_accounts()[$userId] ?? null;
        if (
            is_array($stored)
            && !empty($stored['account_id'])
            && empty($stored['disconnected_at'])
            && empty($stored['invalid_at'])
        ) {
            cde_salesnav_set_session_account(
                (string) $stored['account_id'],
                (string) ($stored['label'] ?? ''),
                (string) ($stored['avatar_url'] ?? '')
            );
            $accountId = (string) $stored['account_id'];
        }
    } else {
        $userId = cde_salesnav_user_id();
        $stored = cde_salesnav_load_accounts()[$userId] ?? null;
        $sessionAvatar = trim((string) ($_SESSION['salesnav_account_avatar'] ?? ''));
        if ($sessionAvatar === '' && is_array($stored)) {
            if (!empty($stored['avatar_url'])) {
                $_SESSION['salesnav_account_avatar'] = (string) $stored['avatar_url'];
            }
            if (trim((string) ($_SESSION['salesnav_account_label'] ?? '')) === '' && !empty($stored['label'])) {
                $_SESSION['salesnav_account_label'] = (string) $stored['label'];
            }
        }
        if (trim((string) ($_SESSION['salesnav_account_avatar'] ?? '')) === '') {
            foreach (cde_salesnav_load_accounts() as $row) {
                if (!is_array($row) || ($row['account_id'] ?? '') !== $accountId) {
                    continue;
                }
                if (!empty($row['avatar_url'])) {
                    $_SESSION['salesnav_account_avatar'] = (string) $row['avatar_url'];
                }
                if (trim((string) ($_SESSION['salesnav_account_label'] ?? '')) === '' && !empty($row['label'])) {
                    $_SESSION['salesnav_account_label'] = (string) $row['label'];
                }
                break;
            }
        }
    }
    if ($accountId === '') {
        return null;
    }
    return [
        'account_id' => $accountId,
        'label' => trim((string) ($_SESSION['salesnav_account_label'] ?? '')),
        'avatar_url' => trim((string) ($_SESSION['salesnav_account_avatar'] ?? '')),
        'connected_at' => (string) ($_SESSION['salesnav_connected_at'] ?? ''),
    ];
}

function cde_salesnav_require_account(): array
{
    $account = cde_salesnav_session_account();
    if ($account === null || $account['account_id'] === '') {
        cde_json_response(403, [
            'ok' => false,
            'error' => 'Connect your LinkedIn / Sales Navigator account before exporting.',
            'needs_connect' => true,
        ]);
    }
    return $account;
}

function cde_salesnav_notify_secret(): string
{
    $cfg = cde_unipile_api_config();
    if ($cfg['notify_secret'] !== '') {
        return $cfg['notify_secret'];
    }
    return hash('sha256', $cfg['api_key'] . '|salesnav-notify');
}

function cde_salesnav_site_origin(): string
{
    $cfg = cde_unipile_api_config();
    return rtrim($cfg['site_origin'], '/');
}

function cde_salesnav_fetch_account_label(array $config, string $accountId): string
{
    return cde_salesnav_fetch_account_meta($config, $accountId)['label'];
}

/** @return array{label: string, avatar_url: string} */
function cde_salesnav_fetch_account_meta(array $config, string $accountId): array
{
    $meta = ['label' => '', 'avatar_url' => ''];

    $resp = cde_unipile_request($config, 'GET', '/users/me', ['account_id' => $accountId]);
    if ($resp['ok']) {
        $profile = $resp['data'];
        if (isset($profile['data']) && is_array($profile['data'])) {
            $profile = $profile['data'];
        }
        if (is_array($profile)) {
            $meta['avatar_url'] = cde_salesnav_avatar_from_profile($profile);
            $first = trim((string) ($profile['first_name'] ?? ''));
            $last = trim((string) ($profile['last_name'] ?? ''));
            $full = trim($first . ' ' . $last);
            if ($full !== '') {
                $meta['label'] = $full;
            } elseif (!empty($profile['name'])) {
                $meta['label'] = trim((string) $profile['name']);
            }
        }
    }

    if ($meta['label'] === '') {
        $resp = cde_unipile_request($config, 'GET', '/accounts/' . rawurlencode($accountId));
        if ($resp['ok']) {
            $item = $resp['data'];
            if (isset($item['data']) && is_array($item['data'])) {
                $item = $item['data'];
            }
            if (is_array($item)) {
                $meta['label'] = cde_salesnav_account_label_from_item($item);
            }
        }
    }

    return $meta;
}

function cde_salesnav_avatar_from_profile(array $profile): string
{
    foreach (['profile_picture_url_large', 'profile_picture_url', 'public_picture_url'] as $key) {
        $url = trim((string) ($profile[$key] ?? ''));
        if ($url !== '' && preg_match('#^https?://#i', $url)) {
            return $url;
        }
    }
    return '';
}

function cde_salesnav_refresh_account_meta(string $userId, string $accountId): array
{
    return cde_salesnav_apply_unipile_account($userId, $accountId);
}

function cde_salesnav_account_label_from_item(array $item): string
{
    $params = $item['connection_params']['im'] ?? [];
    if (is_array($params)) {
        $username = trim((string) ($params['username'] ?? $params['publicIdentifier'] ?? ''));
        if ($username !== '') {
            return $username;
        }
    }
    $name = trim((string) ($item['name'] ?? ''));
    return $name !== '' ? $name : (string) ($item['id'] ?? '');
}

function cde_salesnav_create_hosted_link(string $type = 'create', ?string $reconnectAccountId = null): array
{
    $config = cde_unipile_api_config();
    $userId = cde_salesnav_user_id();
    $origin = cde_salesnav_site_origin();
    $token = cde_salesnav_notify_secret();
    $expires = gmdate('Y-m-d\TH:i:s.v\Z', time() + 900);

    $body = [
        'type' => $type,
        'providers' => ['LINKEDIN'],
        'api_url' => $config['dsn_url'],
        'expiresOn' => $expires,
        'name' => $userId,
        'notify_url' => $origin . '/api/salesnav-unipile-notify.php?token=' . rawurlencode($token),
        'success_redirect_url' => $origin . '/salesnav/connect-callback.html?connected=1',
        'failure_redirect_url' => $origin . '/salesnav/connect-callback.html?connected=0',
        'config' => [
            'linkedin' => [
                'allow_methods' => ['credentials', 'cookies'],
                'products' => ['classic', 'sales_navigator'],
            ],
        ],
    ];

    if ($type === 'reconnect' && $reconnectAccountId) {
        $body['reconnect_account'] = $reconnectAccountId;
    }

    $resp = cde_unipile_request(
        $config,
        'POST',
        '/hosted/accounts/link',
        null,
        $body,
        60
    );

    if (!$resp['ok']) {
        cde_json_response($resp['status'] >= 400 && $resp['status'] < 600 ? $resp['status'] : 502, [
            'ok' => false,
            'error' => $resp['error'] ?? 'Could not start LinkedIn connection.',
        ]);
    }

    $url = (string) ($resp['data']['url'] ?? '');
    if ($url === '') {
        cde_json_response(502, [
            'ok' => false,
            'error' => 'Unipile did not return a connection URL.',
        ]);
    }

    $url = cde_salesnav_apply_hosted_auth_domain($url, $config['hosted_auth_domain'] ?? '');

    return ['url' => $url, 'user_id' => $userId];
}

function cde_salesnav_normalize_list_url(string $value): string
{
    $value = trim($value);
    if (preg_match('#https?://(?:www\.)?linkedin\.com/sales/lists/people/\d+#i', $value, $m)) {
        return $m[0];
    }
    if (ctype_digit($value)) {
        return 'https://www.linkedin.com/sales/lists/people/' . $value;
    }
    cde_json_response(400, [
        'ok' => false,
        'error' => 'Invalid Sales Navigator list URL or list id.',
    ]);
}

function cde_salesnav_normalize_search_url(string $value): string
{
    $value = trim($value);
    if (preg_match('#https?://(?:www\.)?linkedin\.com/sales/search/people#i', $value, $m)) {
        return $value;
    }
    cde_json_response(400, [
        'ok' => false,
        'error' => 'Invalid Sales Navigator search URL.',
    ]);
}

function cde_unipile_account_error_is_stale(array $resp): bool
{
    $status = (int) ($resp['status'] ?? 0);
    if ($status === 404) {
        return true;
    }
    $err = strtolower((string) ($resp['error'] ?? ''));
    return str_contains($err, 'resource not found')
        || str_contains($err, 'not found')
        || str_contains($err, 'expired credentials');
}

function cde_salesnav_stale_account_message(): string
{
    return 'LinkedIn connection expired. Reconnect your account from the panel and try again.';
}

function cde_salesnav_account_revalidate_ttl(): int
{
    return 300;
}

function cde_salesnav_is_account_alive(string $accountId): bool
{
    if ($accountId === '') {
        return false;
    }
    $config = cde_unipile_api_config($accountId);
    $resp = cde_unipile_request($config, 'GET', '/users/me', ['account_id' => $accountId], null, 30);

    return $resp['ok'];
}

/** @return list<array<string, mixed>> */
function cde_salesnav_list_unipile_account_items(): array
{
    $config = cde_unipile_api_config(null);
    $resp = cde_unipile_request($config, 'GET', '/accounts');
    if (!$resp['ok']) {
        return [];
    }
    $items = $resp['data']['items'] ?? $resp['data'] ?? [];

    return is_array($items) ? $items : [];
}

function cde_salesnav_resolve_linked_account_id(string $userId): ?string
{
    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    $storedLabel = is_array($stored) ? trim((string) ($stored['label'] ?? '')) : '';
    $storedAccountId = is_array($stored) ? trim((string) ($stored['account_id'] ?? '')) : '';

    if ($storedAccountId !== '' && cde_salesnav_is_account_alive($storedAccountId)) {
        return $storedAccountId;
    }

    $candidates = [];
    foreach (cde_salesnav_list_unipile_account_items() as $item) {
        if (!is_array($item)) {
            continue;
        }
        $id = trim((string) ($item['id'] ?? $item['account_id'] ?? ''));
        if ($id === '' || !cde_salesnav_is_account_alive($id)) {
            continue;
        }

        $linkedName = trim((string) ($item['name'] ?? ''));
        $meta = cde_salesnav_fetch_account_meta(cde_unipile_api_config($id), $id);
        $label = trim((string) ($meta['label'] ?? ''));

        $score = 0;
        if ($linkedName !== '' && $linkedName === $userId) {
            $score += 100;
        }
        if ($storedLabel !== '' && $label !== '' && strcasecmp($label, $storedLabel) === 0) {
            $score += 50;
        }
        if ($storedAccountId !== '' && $id === $storedAccountId) {
            $score += 10;
        }

        $created = strtotime((string) ($item['created_at'] ?? $item['last_update'] ?? ''));
        $candidates[] = [
            'id' => $id,
            'score' => $score,
            'created' => $created !== false ? $created : 0,
        ];
    }

    if ($candidates === []) {
        return null;
    }

    usort($candidates, static function (array $a, array $b): int {
        if ($a['score'] !== $b['score']) {
            return $b['score'] <=> $a['score'];
        }

        return $b['created'] <=> $a['created'];
    });

    $best = $candidates[0];
    if ($best['score'] <= 0 && count($candidates) > 1) {
        return null;
    }

    return (string) $best['id'];
}

function cde_salesnav_propagate_account_id(string $fromAccountId, string $toAccountId, array $meta): void
{
    if ($fromAccountId === '' || $fromAccountId === $toAccountId) {
        return;
    }

    $all = cde_salesnav_load_accounts();
    $changed = false;
    foreach ($all as $uid => $rec) {
        if (!is_array($rec) || (string) ($rec['account_id'] ?? '') !== $fromAccountId) {
            continue;
        }
        $all[$uid] = array_merge($rec, [
            'account_id' => $toAccountId,
            'label' => ($meta['label'] ?? '') !== '' ? $meta['label'] : (string) ($rec['label'] ?? ''),
            'avatar_url' => (string) ($meta['avatar_url'] ?? $rec['avatar_url'] ?? ''),
            'linked_at' => gmdate('c'),
            'status' => 'CONNECTED',
            'disconnected_at' => null,
            'invalid_at' => null,
            'invalid_reason' => null,
            'validated_at' => gmdate('c'),
            'previous_account_id' => $fromAccountId,
        ]);
        $changed = true;
    }
    if (!$changed) {
        return;
    }
    $path = cde_salesnav_accounts_file();
    @file_put_contents($path, json_encode($all, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

/** @return array{label: string, avatar_url: string} */
function cde_salesnav_apply_unipile_account(string $userId, string $accountId): array
{
    $config = cde_unipile_api_config($accountId);
    $meta = cde_salesnav_fetch_account_meta($config, $accountId);
    $stored = cde_salesnav_load_accounts()[$userId] ?? [];
    if (!is_array($stored)) {
        $stored = [];
    }

    $previous = trim((string) ($stored['account_id'] ?? ''));
    if ($previous !== '' && $previous !== $accountId) {
        cde_salesnav_propagate_account_id($previous, $accountId, $meta);
        $stored = cde_salesnav_load_accounts()[$userId] ?? $stored;
        if (!is_array($stored)) {
            $stored = [];
        }
    }

    cde_salesnav_save_account($userId, array_merge($stored, [
        'account_id' => $accountId,
        'label' => $meta['label'] !== '' ? $meta['label'] : (string) ($stored['label'] ?? ''),
        'avatar_url' => $meta['avatar_url'] !== '' ? $meta['avatar_url'] : (string) ($stored['avatar_url'] ?? ''),
        'linked_at' => gmdate('c'),
        'status' => 'CONNECTED',
        'disconnected_at' => null,
        'invalid_at' => null,
        'invalid_reason' => null,
        'validated_at' => gmdate('c'),
        'previous_account_id' => $previous !== '' && $previous !== $accountId ? $previous : ($stored['previous_account_id'] ?? null),
    ]));

    if (cde_salesnav_user_id() === $userId) {
        cde_salesnav_set_session_account(
            $accountId,
            $meta['label'] !== '' ? $meta['label'] : (string) ($stored['label'] ?? ''),
            $meta['avatar_url'] !== '' ? $meta['avatar_url'] : (string) ($stored['avatar_url'] ?? '')
        );
    }

    return $meta;
}

function cde_salesnav_should_revalidate_account(?array $stored): bool
{
    if (!is_array($stored) || empty($stored['account_id']) || !empty($stored['invalid_at'])) {
        return false;
    }
    $validated = strtotime((string) ($stored['validated_at'] ?? ''));
    if ($validated === false) {
        return true;
    }

    return (time() - $validated) >= cde_salesnav_account_revalidate_ttl();
}

function cde_salesnav_touch_account_validated(string $userId): void
{
    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    if (!is_array($stored)) {
        return;
    }
    cde_salesnav_save_account($userId, array_merge($stored, [
        'validated_at' => gmdate('c'),
        'status' => 'CONNECTED',
        'invalid_at' => null,
        'invalid_reason' => null,
    ]));
}

function cde_salesnav_mark_account_stale(?string $userId = null, string $reason = ''): void
{
    $userId = $userId ?? cde_salesnav_user_id();
    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    if (!is_array($stored)) {
        cde_salesnav_clear_session_account();
        return;
    }
    cde_salesnav_save_account($userId, array_merge($stored, [
        'disconnected_at' => gmdate('c'),
        'invalid_at' => gmdate('c'),
        'invalid_reason' => $reason !== '' ? $reason : 'LinkedIn connection is no longer valid in Unipile.',
        'status' => 'INVALID',
    ]));
    cde_salesnav_clear_session_account();
}

function cde_salesnav_handle_stale_unipile_response(array $resp, ?string $userId = null): bool
{
    if (!cde_unipile_account_error_is_stale($resp)) {
        return false;
    }
    cde_salesnav_mark_account_stale($userId, (string) ($resp['error'] ?? ''));

    return true;
}

/** @return array{account_id: string, label: string, avatar_url: string, connected_at: string}|null */
function cde_salesnav_ensure_account_valid(?string $userId = null): ?array
{
    $userId = $userId ?? cde_salesnav_user_id();
    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    if (is_array($stored) && !empty($stored['invalid_at'])) {
        cde_salesnav_clear_session_account();
        return null;
    }

    $account = cde_salesnav_session_account();
    if ($account === null || ($account['account_id'] ?? '') === '') {
        return null;
    }

    if (cde_salesnav_should_revalidate_account($stored)) {
        if (!cde_salesnav_is_account_alive((string) $account['account_id'])) {
            cde_salesnav_mark_account_stale($userId);
            return null;
        }
        cde_salesnav_touch_account_validated($userId);
    }

    return $account;
}

/** @return array{account_id: string, label: string, avatar_url: string, connected_at: string} */
function cde_salesnav_require_valid_account(): array
{
    $userId = cde_salesnav_user_id();
    $account = cde_salesnav_ensure_account_valid($userId);
    if ($account !== null) {
        return $account;
    }

    $stored = cde_salesnav_load_accounts()[$userId] ?? null;
    $hadLink = is_array($stored) && (!empty($stored['account_id']) || !empty($stored['label']));
    cde_json_response(403, [
        'ok' => false,
        'error' => cde_salesnav_stale_account_message(),
        'needs_connect' => true,
        'needs_reconnect' => $hadLink,
        'reconnect_available' => $hadLink,
        'stored_label' => is_array($stored) ? (string) ($stored['label'] ?? '') : '',
    ]);
}

/** Background exports must throw so task status can be updated. */
function cde_salesnav_export_abort(string $error, ?array $resp = null): void
{
    if (is_array($resp) && cde_unipile_account_error_is_stale($resp)) {
        throw new RuntimeException(cde_salesnav_stale_account_message());
    }
    throw new RuntimeException($error);
}

function cde_unipile_request(
    array $config,
    string $method,
    string $path,
    ?array $query = null,
    ?array $body = null,
    int $timeout = 120
): array {
    $url = $config['base'] . $path;
    if ($query) {
        $parts = [];
        foreach ($query as $k => $v) {
            $parts[] = $k === 'cursor'
                ? rawurlencode($k) . '=' . rawurlencode((string) $v)
                : rawurlencode($k) . '=' . rawurlencode((string) $v);
        }
        $url .= '?' . implode('&', $parts);
    }

    $headers = [
        'X-API-KEY: ' . $config['api_key'],
        'Accept: application/json',
    ];

    $ch = curl_init($url);
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => strtoupper($method),
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_CONNECTTIMEOUT => 30,
    ];

    if ($body !== null) {
        $json = json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $headers[] = 'Content-Type: application/json';
        $opts[CURLOPT_HTTPHEADER] = $headers;
        $opts[CURLOPT_POSTFIELDS] = $json;
    }

    curl_setopt_array($ch, $opts);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'status' => 0, 'error' => $err ?: 'Unipile request failed'];
    }

    $data = json_decode((string) $raw, true);
    if (!is_array($data)) {
        $data = [];
    }

    if ($code >= 400) {
        $msg = $data['title'] ?? $data['error'] ?? $data['message'] ?? 'Unipile API error';
        return ['ok' => false, 'status' => $code, 'error' => (string) $msg, 'data' => $data];
    }

    return ['ok' => true, 'status' => $code, 'data' => $data];
}

function cde_salesnav_collect_items(array $page): array
{
    foreach (['items', 'data', 'results', 'leads'] as $key) {
        if (isset($page[$key]) && is_array($page[$key])) {
            return $page[$key];
        }
    }
    return [];
}

function cde_salesnav_flatten_lead(array $item): array
{
    $company = $item['company'] ?? [];
    if (is_string($company)) {
        $company = ['name' => $company];
    }
    if (!is_array($company)) {
        $company = [];
    }

    $positions = $item['current_positions'] ?? $item['positions'] ?? [];
    $role = '';
    $companyName = (string) ($company['name'] ?? $item['company_name'] ?? '');
    if (is_array($positions) && isset($positions[0]) && is_array($positions[0])) {
        $role = (string) ($positions[0]['role'] ?? $positions[0]['title'] ?? '');
        if ($companyName === '') {
            $companyName = (string) ($positions[0]['company'] ?? '');
        }
    }

    $name = (string) ($item['name'] ?? '');
    $parts = $name !== '' ? preg_split('/\s+/', $name, 2) : ['', ''];
    $first = (string) ($item['first_name'] ?? ($parts[0] ?? ''));
    $last = (string) ($item['last_name'] ?? ($parts[1] ?? ''));

    return [
        'first_name' => $first,
        'last_name' => $last,
        'full_name' => $name !== '' ? $name : trim($first . ' ' . $last),
        'job_title' => (string) ($item['headline'] ?? $role ?? $item['title'] ?? ''),
        'company_name' => $companyName,
        'location' => (string) ($item['location'] ?? ''),
        'linkedin_url' => (string) ($item['public_profile_url'] ?? $item['profile_url'] ?? $item['linkedin_url'] ?? ''),
        'sales_nav_id' => (string) ($item['id'] ?? $item['member_id'] ?? ''),
        'open_profile' => (string) ($item['open_profile'] ?? $item['open_link'] ?? ''),
        'connection_degree' => (string) ($item['network_distance'] ?? $item['degree'] ?? ''),
    ];
}

function cde_salesnav_paginate_v1(array $config, string $sourceUrl, int $maxLeads): array
{
    $collected = [];
    $cursor = null;

    while (count($collected) < $maxLeads) {
        $pageSize = min(25, $maxLeads - count($collected));
        $query = [
            'account_id' => $config['account_id'],
            'limit' => $pageSize,
        ];
        if ($cursor !== null) {
            $query['cursor'] = $cursor;
        }

        $resp = cde_unipile_request(
            $config,
            'POST',
            '/linkedin/search',
            $query,
            ['url' => $sourceUrl]
        );
        if (!$resp['ok']) {
            cde_salesnav_export_abort($resp['error'] ?? 'Export failed', $resp);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $cursor = $resp['data']['cursor'] ?? $resp['data']['next_cursor'] ?? null;
        if ($cursor === null || $cursor === '') {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_paginate_v2_search(array $config, string $searchUrl, int $maxLeads): array
{
    $collected = [];
    $cursor = null;
    $limit = min(100, $maxLeads);

    while (count($collected) < $maxLeads) {
        $query = ['limit' => $limit];
        if ($cursor !== null) {
            $query['cursor'] = $cursor;
        }

        $resp = cde_unipile_request(
            $config,
            'POST',
            '/' . rawurlencode($config['account_id']) . '/linkedin/sales-navigator/search',
            $query,
            ['url' => $searchUrl]
        );
        if (!$resp['ok']) {
            cde_salesnav_export_abort($resp['error'] ?? 'Export failed', $resp);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $cursor = $resp['data']['next_cursor'] ?? $resp['data']['cursor'] ?? null;
        if ($cursor === null || $cursor === '' || count($batch) < $limit) {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_paginate_v2_list(array $config, string $listId, int $maxLeads): array
{
    $collected = [];
    $offset = 0;
    $limit = min(100, $maxLeads);

    while (count($collected) < $maxLeads) {
        $resp = cde_unipile_request(
            $config,
            'POST',
            '/' . rawurlencode($config['account_id']) . '/linkedin/sales-navigator/lead-lists/' . rawurlencode($listId),
            ['limit' => $limit, 'offset' => $offset],
            []
        );
        if (!$resp['ok']) {
            cde_salesnav_export_abort($resp['error'] ?? 'Export failed', $resp);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $offset += count($batch);
        if (count($batch) < $limit) {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_export(array $config, string $sourceUrl, string $mode, int $maxLeads): array
{
    if ($config['is_v1']) {
        return cde_salesnav_paginate_v1($config, $sourceUrl, $maxLeads);
    }

    if ($mode === 'search') {
        return cde_salesnav_paginate_v2_search($config, $sourceUrl, $maxLeads);
    }

    if (preg_match('#linkedin\.com/sales/lists/people/(?P<id>\d+)#i', $sourceUrl, $m)) {
        return cde_salesnav_paginate_v2_list($config, $m['id'], $maxLeads);
    }

    return cde_salesnav_paginate_v2_search($config, $sourceUrl, $maxLeads);
}

function cde_enforce_salesnav_rate_limits(int $limit): void
{
    $ip = cde_client_ip();
    cde_session_start();
    $sid = session_id() ?: $ip;

    if ($limit <= 25) {
        $checks = [
            cde_rate_consume('salesnav_demo_ip_hour', $ip, 8, 3600),
            cde_rate_consume('salesnav_demo_ip_day', $ip, 25, 86400),
            cde_rate_consume('salesnav_demo_sess', $sid, 5, 900),
        ];
    } else {
        $checks = [
            cde_rate_consume('salesnav_full_ip_hour', $ip, 3, 3600),
            cde_rate_consume('salesnav_full_ip_day', $ip, 10, 86400),
            cde_rate_consume('salesnav_full_sess', $sid, 2, 900),
        ];
    }

    foreach ($checks as $check) {
        if (!$check['ok']) {
            cde_json_response(429, [
                'ok' => false,
                'error' => 'Rate limit reached. Try again later or request volume access below.',
                'retry_after' => $check['retry_after'],
            ]);
        }
    }
}
