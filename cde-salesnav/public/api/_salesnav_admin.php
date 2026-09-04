<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_credits.php';
require_once __DIR__ . '/_tasks.php';

const CDE_ADMIN_SESSION_HOURS = 12;

function cde_sn_admin_secret(): string
{
    $env = cde_unipile_read_env();
    return trim((string) ($env['SALESNAV_ADMIN_SECRET'] ?? getenv('SALESNAV_ADMIN_SECRET') ?: ''));
}

/** Plain password or bcrypt hash ($2y$…) from SALESNAV_ADMIN_PASSWORD; falls back to legacy secret. */
function cde_sn_admin_password(): string
{
    $env = cde_unipile_read_env();
    $pass = trim((string) ($env['SALESNAV_ADMIN_PASSWORD'] ?? getenv('SALESNAV_ADMIN_PASSWORD') ?: ''));
    if ($pass !== '') {
        return $pass;
    }

    return cde_sn_admin_secret();
}

function cde_sn_admin_configured(): bool
{
    return cde_sn_admin_emails() !== [] || cde_sn_admin_password() !== '';
}

/** @return list<string> lowercase emails allowed to use panel credentials for admin */
function cde_sn_admin_emails(): array
{
    $env = cde_unipile_read_env();
    $raw = trim((string) ($env['SALESNAV_ADMIN_EMAILS'] ?? getenv('SALESNAV_ADMIN_EMAILS') ?: ''));
    if ($raw === '') {
        return [];
    }
    $out = [];
    foreach (preg_split('/[\s,;]+/', $raw) ?: [] as $part) {
        $email = cde_customer_validate_email((string) $part);
        if ($email !== null) {
            $out[$email] = $email;
        }
    }

    return array_values($out);
}

function cde_sn_admin_panel_login_valid(string $email, string $password): bool
{
    $email = cde_customer_validate_email($email) ?? '';
    if ($email === '' || $password === '') {
        return false;
    }
    $allowed = cde_sn_admin_emails();
    if ($allowed === [] || !in_array($email, $allowed, true)) {
        return false;
    }
    $row = cde_customer_get_by_email($email);
    if (!is_array($row) || empty($row['password_hash']) || !is_string($row['password_hash'])) {
        return false;
    }

    return password_verify($password, $row['password_hash']);
}

function cde_sn_admin_password_valid(?string $password): bool
{
    $expected = cde_sn_admin_password();
    if ($expected === '' || $password === null || $password === '') {
        return false;
    }
    $password = trim($password);
    if (str_starts_with($expected, '$2y$') || str_starts_with($expected, '$2a$')) {
        return password_verify($password, $expected);
    }

    return hash_equals($expected, $password);
}

function cde_sn_admin_session_valid(): bool
{
    cde_session_start();
    if (empty($_SESSION['salesnav_admin_ok'])) {
        return false;
    }
    $at = (int) ($_SESSION['salesnav_admin_at'] ?? 0);
    if ($at <= 0 || (time() - $at) > CDE_ADMIN_SESSION_HOURS * 3600) {
        cde_sn_admin_logout();
        return false;
    }

    return true;
}

function cde_sn_admin_token_valid(?string $token): bool
{
    return cde_sn_admin_password_valid($token);
}

function cde_sn_admin_require_auth(): void
{
    $header = trim((string) ($_SERVER['HTTP_X_SALESNAV_ADMIN_TOKEN'] ?? ''));
    if (cde_sn_admin_token_valid($header)) {
        return;
    }
    if (cde_sn_admin_session_valid()) {
        return;
    }
    cde_json_response(401, ['ok' => false, 'error' => 'Unauthorized']);
}

function cde_sn_admin_login(string $password): bool
{
    if (!cde_sn_admin_password_valid($password)) {
        return false;
    }
    cde_session_start();
    $_SESSION['salesnav_admin_ok'] = true;
    $_SESSION['salesnav_admin_at'] = time();
    unset($_SESSION['salesnav_admin_email']);

    return true;
}

function cde_sn_admin_login_with_panel(string $email, string $password): bool
{
    if (!cde_sn_admin_panel_login_valid($email, $password)) {
        return false;
    }
    cde_session_start();
    $_SESSION['salesnav_admin_ok'] = true;
    $_SESSION['salesnav_admin_at'] = time();
    $_SESSION['salesnav_admin_email'] = cde_customer_validate_email($email);

    return true;
}

function cde_sn_admin_logout(): void
{
    cde_session_start();
    unset($_SESSION['salesnav_admin_ok'], $_SESSION['salesnav_admin_at'], $_SESSION['salesnav_admin_email']);
}

/** @return array<string, string> user_id => email */
function cde_sn_admin_email_index(): array
{
    $map = [];
    foreach (cde_customers_load() as $uid => $row) {
        if (!is_array($row)) {
            continue;
        }
        $email = cde_customer_normalize_email((string) ($row['email'] ?? ''));
        if ($email !== '') {
            $map[(string) $uid] = $email;
        }
    }
    foreach (cde_tasks_load_all() as $task) {
        if (!is_array($task)) {
            continue;
        }
        $uid = (string) ($task['user_id'] ?? '');
        $email = cde_customer_normalize_email((string) ($task['email'] ?? ''));
        if ($uid !== '' && $email !== '') {
            $map[$uid] = $email;
        }
    }

    return $map;
}

function cde_sn_admin_resolve_user_id(?string $userId, ?string $email): ?string
{
    $userId = trim((string) $userId);
    $email = cde_customer_validate_email((string) $email) ?? '';
    if ($email !== '') {
        return cde_salesnav_user_id_for_email($email);
    }
    if ($userId !== '') {
        return $userId;
    }

    return null;
}

function cde_sn_admin_ledger_kind(string $ref, int $delta): string
{
    if (str_starts_with($ref, 'stripe:')) {
        return 'topup';
    }
    if (str_starts_with($ref, 'admin:') || str_contains($ref, 'grant')) {
        return 'grant';
    }
    if (str_starts_with($ref, 'export:')) {
        return 'spend';
    }
    if (str_starts_with($ref, 'refund:')) {
        return 'refund';
    }
    if (str_starts_with($ref, 'merge:')) {
        return 'merge';
    }
    if ($delta > 0) {
        return 'credit';
    }
    if ($delta < 0) {
        return 'debit';
    }

    return 'other';
}

/** @return list<array<string, mixed>> newest first */
function cde_sn_admin_read_ledger(int $limit = 150, ?string $userId = null, ?string $kind = null): array
{
    $limit = max(1, min(500, $limit));
    $path = cde_credits_ledger_file();
    if (!is_readable($path)) {
        return [];
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if (!is_array($lines)) {
        return [];
    }

    $emailIndex = cde_sn_admin_email_index();
    $out = [];
    for ($i = count($lines) - 1; $i >= 0 && count($out) < $limit; $i--) {
        $entry = json_decode($lines[$i], true);
        if (!is_array($entry)) {
            continue;
        }
        $uid = (string) ($entry['user_id'] ?? '');
        if ($userId !== null && $userId !== '' && $uid !== $userId) {
            continue;
        }
        $delta = (int) ($entry['delta'] ?? 0);
        $ref = (string) ($entry['ref'] ?? '');
        $entryKind = cde_sn_admin_ledger_kind($ref, $delta);
        if ($kind !== null && $kind !== '' && $kind !== 'all' && $entryKind !== $kind) {
            continue;
        }
        $meta = is_array($entry['meta'] ?? null) ? $entry['meta'] : [];
        $email = strtolower((string) ($meta['email'] ?? $emailIndex[$uid] ?? ''));
        $out[] = [
            'ts' => (string) ($entry['ts'] ?? ''),
            'user_id' => $uid,
            'email' => $email,
            'delta' => $delta,
            'balance' => (int) ($entry['balance'] ?? 0),
            'ref' => $ref,
            'kind' => $entryKind,
            'meta' => $meta,
        ];
    }

    return $out;
}

/** @return list<array<string, mixed>> */
function cde_sn_admin_list_tasks(int $limit = 100, ?string $userId = null, ?string $status = null): array
{
    $limit = max(1, min(500, $limit));
    $emailIndex = cde_sn_admin_email_index();
    $out = [];
    foreach (cde_tasks_load_all() as $taskId => $task) {
        if (!is_array($task)) {
            continue;
        }
        $uid = (string) ($task['user_id'] ?? '');
        if ($userId !== null && $userId !== '' && $uid !== $userId) {
            continue;
        }
        $taskStatus = (string) ($task['status'] ?? 'processing');
        if ($status !== null && $status !== '' && $status !== 'all' && $taskStatus !== $status) {
            continue;
        }
        $email = cde_customer_normalize_email((string) ($task['email'] ?? $emailIndex[$uid] ?? ''));
        $out[] = [
            'id' => $taskId,
            'user_id' => $uid,
            'email' => $email,
            'status' => $taskStatus,
            'source_label' => (string) ($task['source_label'] ?? ''),
            'mode' => (string) ($task['mode'] ?? ''),
            'lead_count' => (int) ($task['lead_count'] ?? 0),
            'credits_used' => (int) ($task['credits_used'] ?? 0),
            'error' => (string) ($task['error'] ?? ''),
            'created_at' => (string) ($task['created_at'] ?? ''),
            'completed_at' => (string) ($task['completed_at'] ?? ''),
        ];
    }
    usort($out, static fn ($a, $b) => strcmp((string) ($b['created_at'] ?? ''), (string) ($a['created_at'] ?? '')));

    return array_slice($out, 0, $limit);
}

/** @return list<array<string, mixed>> */
function cde_sn_admin_build_users_index(): array
{
    $users = [];
    $ensure = static function (string $userId) use (&$users): string {
        if (!isset($users[$userId])) {
            $users[$userId] = [
                'user_id' => $userId,
                'email' => '',
                'email_verified' => false,
                'has_password' => false,
                'created_at' => '',
                'balance' => 0,
                'wallet_updated_at' => '',
                'linkedin_connected' => false,
                'linkedin_invalid' => false,
                'linkedin_label' => '',
                'task_count' => 0,
                'tasks_ready' => 0,
                'tasks_failed' => 0,
                'tasks_processing' => 0,
                'credits_purchased' => 0,
                'credits_granted' => 0,
                'credits_spent' => 0,
            ];
        }

        return $userId;
    };

    foreach (cde_customers_load() as $uid => $row) {
        if (!is_array($row)) {
            continue;
        }
        $key = $ensure((string) $uid);
        $users[$key]['email'] = cde_customer_normalize_email((string) ($row['email'] ?? ''));
        $users[$key]['email_verified'] = !empty($row['email_verified']);
        $users[$key]['has_password'] = !empty($row['password_hash']);
        $users[$key]['created_at'] = (string) ($row['created_at'] ?? '');
    }

    foreach (cde_credits_load_wallets() as $uid => $wallet) {
        if (!is_array($wallet)) {
            continue;
        }
        $key = $ensure((string) $uid);
        $users[$key]['balance'] = max(0, (int) ($wallet['balance'] ?? 0));
        $users[$key]['wallet_updated_at'] = (string) ($wallet['updated_at'] ?? '');
    }

    foreach (cde_salesnav_load_accounts() as $uid => $acc) {
        if (!is_array($acc)) {
            continue;
        }
        $key = $ensure((string) $uid);
        if ($users[$key]['email'] === '' && !empty($acc['email'])) {
            $users[$key]['email'] = cde_customer_normalize_email((string) $acc['email']);
        }
        $users[$key]['linkedin_connected'] = empty($acc['invalid_at']) && !empty($acc['account_id']);
        $users[$key]['linkedin_invalid'] = !empty($acc['invalid_at']);
        $users[$key]['linkedin_label'] = (string) ($acc['label'] ?? $acc['account_id'] ?? '');
    }

    foreach (cde_tasks_load_all() as $task) {
        if (!is_array($task)) {
            continue;
        }
        $uid = (string) ($task['user_id'] ?? '');
        if ($uid === '') {
            continue;
        }
        $key = $ensure($uid);
        $email = cde_customer_normalize_email((string) ($task['email'] ?? ''));
        if ($email !== '') {
            $users[$key]['email'] = $email;
        }
        $users[$key]['task_count']++;
        $status = (string) ($task['status'] ?? '');
        if ($status === 'ready') {
            $users[$key]['tasks_ready']++;
        } elseif ($status === 'failed') {
            $users[$key]['tasks_failed']++;
        } elseif ($status === 'processing') {
            $users[$key]['tasks_processing']++;
        }
    }

    $path = cde_credits_ledger_file();
    if (is_readable($path)) {
        $handle = fopen($path, 'rb');
        if ($handle !== false) {
            while (($line = fgets($handle)) !== false) {
                $entry = json_decode(trim($line), true);
                if (!is_array($entry)) {
                    continue;
                }
                $uid = (string) ($entry['user_id'] ?? '');
                if ($uid === '') {
                    continue;
                }
                $key = $ensure($uid);
                $delta = (int) ($entry['delta'] ?? 0);
                $ref = (string) ($entry['ref'] ?? '');
                $meta = is_array($entry['meta'] ?? null) ? $entry['meta'] : [];
                if ($users[$key]['email'] === '' && !empty($meta['email'])) {
                    $users[$key]['email'] = cde_customer_normalize_email((string) $meta['email']);
                }
                if ($delta > 0) {
                    if (str_starts_with($ref, 'stripe:')) {
                        $users[$key]['credits_purchased'] += $delta;
                    } elseif (str_starts_with($ref, 'admin:') || str_contains($ref, 'grant')) {
                        $users[$key]['credits_granted'] += $delta;
                    }
                } elseif ($delta < 0) {
                    $users[$key]['credits_spent'] += abs($delta);
                }
            }
            fclose($handle);
        }
    }

    $out = array_values(array_filter(
        $users,
        static fn (array $u): bool => $u['email'] !== ''
            || $u['balance'] > 0
            || $u['task_count'] > 0
            || $u['credits_purchased'] > 0
            || $u['credits_granted'] > 0
    ));

    usort($out, static function (array $a, array $b): int {
        $ta = (string) ($a['wallet_updated_at'] ?: $a['created_at'] ?: '');
        $tb = (string) ($b['wallet_updated_at'] ?: $b['created_at'] ?: '');

        return strcmp($tb, $ta);
    });

    return $out;
}

/** @return array<string, mixed> */
function cde_sn_admin_overview(): array
{
    $users = cde_sn_admin_build_users_index();
    $tasks = cde_sn_admin_list_tasks(500);
    $ledger = cde_sn_admin_read_ledger(500);

    $totalBalance = 0;
    $verifiedUsers = 0;
    foreach ($users as $u) {
        $totalBalance += (int) ($u['balance'] ?? 0);
        if (!empty($u['email_verified'])) {
            $verifiedUsers++;
        }
    }

    $tasksByStatus = ['processing' => 0, 'ready' => 0, 'failed' => 0];
    foreach ($tasks as $t) {
        $s = (string) ($t['status'] ?? 'processing');
        if (isset($tasksByStatus[$s])) {
            $tasksByStatus[$s]++;
        }
    }

    $topups30 = 0;
    $grants30 = 0;
    $spent30 = 0;
    $cutoff = time() - (30 * 86400);
    foreach ($ledger as $entry) {
        $ts = strtotime((string) ($entry['ts'] ?? ''));
        if ($ts === false || $ts < $cutoff) {
            continue;
        }
        $delta = (int) ($entry['delta'] ?? 0);
        $kind = (string) ($entry['kind'] ?? '');
        if ($kind === 'topup' && $delta > 0) {
            $topups30 += $delta;
        } elseif ($kind === 'grant' && $delta > 0) {
            $grants30 += $delta;
        } elseif ($delta < 0) {
            $spent30 += abs($delta);
        }
    }

    return [
        'users_total' => count($users),
        'users_verified' => $verifiedUsers,
        'credits_in_circulation' => $totalBalance,
        'tasks_total' => count($tasks),
        'tasks_by_status' => $tasksByStatus,
        'credits_topup_30d' => $topups30,
        'credits_granted_30d' => $grants30,
        'credits_spent_30d' => $spent30,
        'admin_configured' => cde_sn_admin_configured(),
    ];
}

/** @return array<string, mixed>|null */
function cde_sn_admin_user_detail(string $userId): ?array
{
    $users = cde_sn_admin_build_users_index();
    $match = null;
    foreach ($users as $u) {
        if (($u['user_id'] ?? '') === $userId) {
            $match = $u;
            break;
        }
    }
    if ($match === null) {
        $customer = cde_customers_load()[$userId] ?? null;
        if (!is_array($customer)) {
            return null;
        }
        $match = [
            'user_id' => $userId,
            'email' => cde_customer_normalize_email((string) ($customer['email'] ?? '')),
            'email_verified' => !empty($customer['email_verified']),
            'has_password' => !empty($customer['password_hash']),
            'created_at' => (string) ($customer['created_at'] ?? ''),
            'balance' => cde_credits_get_balance($userId),
        ];
    }

    return [
        'user' => $match,
        'ledger' => cde_sn_admin_read_ledger(50, $userId),
        'tasks' => cde_sn_admin_list_tasks(50, $userId),
        'linkedin' => cde_salesnav_stored_account($userId),
    ];
}

/** @return array{ok: true, email: string, user_id: string, granted: int, balance_before: int, balance: int, ref: string} */
function cde_sn_admin_grant_credits(string $email, int $amount, string $note = '', string $ref = ''): array
{
    $email = cde_customer_validate_email($email) ?? '';
    if ($email === '') {
        cde_json_response(400, ['ok' => false, 'error' => 'Valid email is required.']);
    }
    if ($amount <= 0 || $amount > 500000) {
        cde_json_response(400, ['ok' => false, 'error' => 'Credits must be between 1 and 500000.']);
    }

    $userId = cde_salesnav_user_id_for_email($email);
    $before = cde_credits_get_balance($userId);
    if ($ref === '') {
        $ref = 'admin:grant:' . hash('sha256', $email . '|' . $amount . '|' . gmdate('Y-m-d\TH:i:s') . '|' . bin2hex(random_bytes(8)));
    }
    $meta = ['email' => $email, 'source' => 'salesnav-admin'];
    if ($note !== '') {
        $meta['note'] = $note;
    }

    $after = cde_credits_add($userId, $amount, $ref, $meta);

    return [
        'ok' => true,
        'email' => $email,
        'user_id' => $userId,
        'granted' => $amount,
        'balance_before' => $before,
        'balance' => $after,
        'ref' => $ref,
    ];
}
