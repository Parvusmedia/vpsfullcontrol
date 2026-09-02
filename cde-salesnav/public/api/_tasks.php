<?php
declare(strict_types=1);

require_once __DIR__ . '/_credits.php';
require_once __DIR__ . '/_harvest.php';
require_once __DIR__ . '/_icypeas.php';
require_once __DIR__ . '/_mail.php';

const CDE_TASKS_MAX_LIMIT = 2000;

function cde_tasks_store_file(): string
{
    return cde_salesnav_private_dir() . '/salesnav_tasks.json';
}

function cde_tasks_exports_dir(): string
{
    $dir = cde_salesnav_private_dir() . '/salesnav_exports';
    if (!is_dir($dir)) {
        @mkdir($dir, 0700, true);
    }
    return $dir;
}

function cde_tasks_load_all(): array
{
    $path = cde_tasks_store_file();
    if (!is_readable($path)) {
        return [];
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

function cde_tasks_save_all(array $tasks): void
{
    $path = cde_tasks_store_file();
    @file_put_contents($path, json_encode($tasks, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

function cde_tasks_new_id(): string
{
    return 'tsk_' . bin2hex(random_bytes(8));
}

function cde_tasks_normalize_limit($raw): int
{
    if ($raw === 'all' || $raw === 'todos' || $raw === 0 || $raw === '0') {
        return CDE_TASKS_MAX_LIMIT;
    }
    $limit = (int) $raw;
    if ($limit < 1) {
        return 50;
    }
    return min($limit, CDE_TASKS_MAX_LIMIT);
}

function cde_tasks_limit_label(int $limit, $raw): string
{
    if ($raw === 'all' || $raw === 'todos' || $raw === 0 || $raw === '0') {
        return 'all';
    }
    return (string) $limit;
}

/** @return array<string, mixed>|null */
function cde_tasks_get(string $taskId, ?string $userId = null): ?array
{
    $task = cde_tasks_load_all()[$taskId] ?? null;
    if (!is_array($task)) {
        return null;
    }
    if ($userId !== null && (string) ($task['user_id'] ?? '') !== $userId) {
        return null;
    }
    return $task;
}

function cde_tasks_for_user(string $userId): array
{
    cde_tasks_recover_stale();
    $out = [];
    foreach (cde_tasks_load_all() as $id => $task) {
        if (!is_array($task) || (string) ($task['user_id'] ?? '') !== $userId) {
            continue;
        }
        $task['id'] = $id;
        $out[] = cde_tasks_public_view($task);
    }
    usort($out, static fn ($a, $b) => strcmp((string) ($b['created_at'] ?? ''), (string) ($a['created_at'] ?? '')));
    return $out;
}

/** @param array<string, mixed> $task */
function cde_tasks_public_view(array $task): array
{
    return [
        'id' => (string) ($task['id'] ?? ''),
        'status' => (string) ($task['status'] ?? 'processing'),
        'mode' => (string) ($task['mode'] ?? ''),
        'source_label' => (string) ($task['source_label'] ?? ''),
        'limit' => (int) ($task['limit'] ?? 0),
        'limit_label' => (string) ($task['limit_label'] ?? ''),
        'lead_count' => (int) ($task['lead_count'] ?? 0),
        'credits_used' => (int) ($task['credits_used'] ?? 0),
        'tier_enriched' => !empty($task['tiers']['enriched']),
        'tier_mail' => !empty($task['tiers']['mail']),
        'emails_found' => (int) ($task['emails_found'] ?? 0),
        'created_at' => (string) ($task['created_at'] ?? ''),
        'completed_at' => (string) ($task['completed_at'] ?? ''),
        'error' => (string) ($task['error'] ?? ''),
        'download_ready' => (string) ($task['status'] ?? '') === 'ready',
    ];
}

/**
 * @return array{error: string, estimated_cost: int, balance: int, profile_count: int}|null
 */
function cde_tasks_credit_preflight(int $limit, array $tiers, ?string $userId = null, ?int $sourceProfileCount = null): ?array
{
    if (!cde_credits_billing_enabled()) {
        return null;
    }
    $userId = $userId ?? cde_salesnav_user_id();
    $profiles = cde_credits_effective_export_profiles($limit, $sourceProfileCount);
    $estimated = cde_credits_estimate_max_export_cost($profiles, $tiers);
    $balance = cde_credits_get_balance($userId);
    if ($balance >= $estimated) {
        return null;
    }

    return [
        'estimated_cost' => $estimated,
        'balance' => $balance,
        'profile_count' => $profiles,
        'error' => cde_credits_insufficient_export_message($profiles, $estimated, $balance),
    ];
}

/** @param array<string, mixed> $payload */
function cde_tasks_create(string $userId, string $email, array $payload): array
{
    $listUrl = trim((string) ($payload['list_url'] ?? ''));
    $searchUrl = trim((string) ($payload['search_url'] ?? ''));
    $limitRaw = $payload['limit'] ?? 50;
    $limit = cde_tasks_normalize_limit($limitRaw);
    $limitLabel = cde_tasks_limit_label($limit, $limitRaw);

    if ($listUrl !== '') {
        $sourceUrl = cde_salesnav_normalize_list_url($listUrl);
        $mode = 'list';
        $sourceLabel = preg_match('#/lists/people/(\d+)#', $sourceUrl, $m) ? 'List ' . $m[1] : 'Lead list';
    } elseif ($searchUrl !== '') {
        $sourceUrl = cde_salesnav_normalize_search_url($searchUrl);
        $mode = 'search';
        $sourceLabel = 'People search';
    } else {
        cde_json_response(400, ['ok' => false, 'error' => 'Provide a Sales Navigator list URL or search URL.']);
    }

    $tiers = cde_credits_parse_tiers($payload);

    $linked = cde_salesnav_session_account();
    $accountId = is_array($linked) ? trim((string) ($linked['account_id'] ?? '')) : '';
    $sourceProfileCount = null;
    if ($accountId !== '') {
        $sourceProfileCount = cde_salesnav_probe_source_profile_count(
            cde_unipile_api_config($accountId),
            $sourceUrl,
            $mode
        );
    }

    $preflight = cde_tasks_credit_preflight($limit, $tiers, $userId, $sourceProfileCount);
    if ($preflight !== null) {
        cde_json_response(402, [
            'ok' => false,
            'needs_payment' => true,
            'estimated_cost' => $preflight['estimated_cost'],
            'balance' => $preflight['balance'],
            'profile_count' => $preflight['profile_count'],
            'error' => $preflight['error'],
        ]);
    }

    $taskId = cde_tasks_new_id();
    $task = [
        'user_id' => $userId,
        'email' => $email,
        'account_id' => $accountId,
        'status' => 'processing',
        'mode' => $mode,
        'source_url' => $sourceUrl,
        'source_label' => $sourceLabel,
        'limit' => $limit,
        'limit_label' => $limitLabel,
        'source_profile_count' => $sourceProfileCount ?? 0,
        'tiers' => $tiers,
        'lead_count' => 0,
        'credits_used' => 0,
        'error' => '',
        'created_at' => gmdate('c'),
        'started_at' => gmdate('c'),
        'completed_at' => '',
    ];

    $all = cde_tasks_load_all();
    $all[$taskId] = $task;
    cde_tasks_save_all($all);

    return ['task_id' => $taskId, 'task' => $task];
}

function cde_tasks_update(string $taskId, array $patch): void
{
    $all = cde_tasks_load_all();
    if (!isset($all[$taskId]) || !is_array($all[$taskId])) {
        return;
    }
    $all[$taskId] = array_merge($all[$taskId], $patch);
    cde_tasks_save_all($all);
}

function cde_tasks_csv_path(string $taskId): string
{
    return cde_tasks_exports_dir() . '/' . preg_replace('/[^a-zA-Z0-9_\-]/', '', $taskId) . '.csv';
}

/** Ensure export CSVs stay readable by the web/PHP user (CLI runs as root otherwise). */
function cde_tasks_fix_export_file_perms(string $path): void
{
    if (!is_file($path)) {
        return;
    }
    $ref = cde_tasks_store_file();
    if (!is_readable($ref)) {
        @chmod($path, 0640);
        return;
    }
    $stat = stat($ref);
    if ($stat === false) {
        @chmod($path, 0640);
        return;
    }
    @chown($path, $stat['uid']);
    @chgrp($path, $stat['gid']);
    @chmod($path, 0600);
}

/** @param array<int, array<string, mixed>> $rows */
function cde_tasks_write_csv(string $taskId, array $rows, array $tiers): void
{
    $basic = ['first_name', 'last_name', 'full_name', 'job_title', 'company_name', 'location', 'linkedin_url', 'sales_nav_id', 'open_profile', 'connection_degree'];
    $enriched = ['company_linkedin_url', 'company_domain', 'company_industry', 'company_size', 'company_hq', 'seniority', 'tenure_years', 'profile_summary', 'skills', 'languages'];
    $mail = cde_icypeas_csv_columns();
    $cols = $basic;
    if (!empty($tiers['enriched'])) {
        $cols = array_merge($cols, $enriched);
    }
    if (!empty($tiers['mail'])) {
        $cols = array_merge($cols, $mail);
    }

    $lines = [implode(',', $cols)];
    foreach ($rows as $row) {
        $cells = [];
        foreach ($cols as $col) {
            $v = (string) ($row[$col] ?? '');
            if (str_contains($v, ',') || str_contains($v, '"') || str_contains($v, "\n")) {
                $v = '"' . str_replace('"', '""', $v) . '"';
            }
            $cells[] = $v;
        }
        $lines[] = implode(',', $cells);
    }
    @file_put_contents(cde_tasks_csv_path($taskId), implode("\n", $lines), LOCK_EX);
    cde_tasks_fix_export_file_perms(cde_tasks_csv_path($taskId));
}

function cde_tasks_panel_url(string $taskId = ''): string
{
    $origin = cde_salesnav_site_origin();
    $url = rtrim($origin, '/') . '/salesnav/panel/';
    if ($taskId !== '') {
        $url .= '?task=' . rawurlencode($taskId);
    }
    return $url;
}

function cde_tasks_send_mail(string $to, string $subject, string $body): void
{
    if ($to === '') {
        return;
    }
    cde_salesnav_send_export_mail($to, $subject, $body);
}

/** Detached CLI worker — survives PHP-FPM request end. */
function cde_tasks_php_cli_bin(): ?string
{
    foreach (['/opt/plesk/php/8.3/bin/php', '/usr/bin/php8.3', '/usr/bin/php'] as $path) {
        if (@is_executable($path)) {
            return $path;
        }
    }
    $bin = PHP_BINARY;
    if ($bin !== '' && stripos($bin, 'fpm') === false && @is_executable($bin)) {
        return $bin;
    }

    return null;
}

function cde_tasks_spawn_run(string $taskId): bool
{
    $script = __DIR__ . '/salesnav-task-run.php';
    if (!is_readable($script)) {
        return false;
    }
    $log = cde_salesnav_private_dir() . '/salesnav_task_runner.log';
    $wrapper = cde_salesnav_private_dir() . '/run-export-task.sh';
    if (is_readable($wrapper)) {
        $cmd = sprintf(
            'nohup /bin/bash %s %s >> %s 2>&1 &',
            escapeshellarg($wrapper),
            escapeshellarg($taskId),
            escapeshellarg($log)
        );
        exec($cmd);

        return true;
    }

    $php = cde_tasks_php_cli_bin();
    if ($php === null) {
        return false;
    }

    $cmd = sprintf(
        'nohup %s %s %s >> %s 2>&1 &',
        escapeshellarg($php),
        escapeshellarg($script),
        escapeshellarg($taskId),
        escapeshellarg($log)
    );
    exec($cmd);

    return true;
}

/** Re-spawn exports stuck in processing after the web worker died. */
function cde_tasks_recover_stale(int $maxAgeSeconds = 900): void
{
    $all = cde_tasks_load_all();
    $now = time();
    foreach ($all as $taskId => $task) {
        if (!is_array($task) || (string) ($task['status'] ?? '') !== 'processing') {
            continue;
        }
        $started = strtotime((string) ($task['started_at'] ?? $task['created_at'] ?? ''));
        if ($started === false || ($now - $started) < $maxAgeSeconds) {
            continue;
        }
        $retries = (int) ($task['run_retries'] ?? 0);
        if ($retries >= 2) {
            $failedTask = array_merge($task, [
                'status' => 'failed',
                'error' => 'Export timed out. Please start a new export from the panel.',
                'completed_at' => gmdate('c'),
            ]);
            cde_tasks_update($taskId, [
                'status' => 'failed',
                'error' => $failedTask['error'],
                'completed_at' => $failedTask['completed_at'],
            ]);
            cde_tasks_notify_failed($failedTask, $taskId, $failedTask['error']);
            continue;
        }
        cde_tasks_update($taskId, ['run_retries' => $retries + 1]);
        cde_tasks_spawn_run($taskId);
    }
}

function cde_tasks_has_mail_tier(array $task): bool
{
    $tiers = is_array($task['tiers'] ?? null) ? $task['tiers'] : [];

    return !empty($tiers['mail']);
}

function cde_tasks_mail_tier_delay_notice(array $task): string
{
    if (!cde_tasks_has_mail_tier($task)) {
        return '';
    }

    return "\nNote: This export includes work email discovery. "
        . "Finding emails can take a few extra minutes — we'll email you again as soon as the CSV is ready.\n";
}

function cde_tasks_notify_started(array $task, string $taskId): void
{
    $email = (string) ($task['email'] ?? '');
    if ($email === '') {
        return;
    }
    $label = (string) ($task['source_label'] ?? 'export');
    $subject = 'Sales Navigator export started — ' . $label;
    $body = "Hello,\n\nYour export task has started.\n\n"
        . "Task: {$label}\n"
        . "Max leads: " . ($task['limit_label'] === 'all' ? 'All (up to 2,000)' : (string) $task['limit']) . "\n"
        . cde_tasks_mail_tier_delay_notice($task) . "\n"
        . "We will email you again when the CSV is ready.\n"
        . "Panel: " . cde_tasks_panel_url() . "\n";
    cde_tasks_send_mail($email, $subject, $body);
}

function cde_tasks_notify_ready(array $task, string $taskId): void
{
    $email = (string) ($task['email'] ?? '');
    if ($email === '') {
        return;
    }
    $label = (string) ($task['source_label'] ?? 'export');
    $count = (int) ($task['lead_count'] ?? 0);
    $subject = 'Sales Navigator export ready — ' . $count . ' leads';
    $body = "Hello,\n\nYour export is ready.\n\n"
        . "Task: {$label}\n"
        . "Leads exported: {$count}\n"
        . "Credits used: " . (int) ($task['credits_used'] ?? 0) . "\n\n"
        . "Download from your panel:\n"
        . cde_tasks_panel_url($taskId) . "\n";
    cde_tasks_send_mail($email, $subject, $body);
}

function cde_tasks_notify_failed(array $task, string $taskId, string $error): void
{
    $email = (string) ($task['email'] ?? '');
    if ($email === '') {
        return;
    }
    $subject = 'Sales Navigator export failed';
    $body = "Hello,\n\nYour export could not be completed.\n\n"
        . "Reason: {$error}\n\n"
        . "Panel: " . cde_tasks_panel_url() . "\n";
    cde_tasks_send_mail($email, $subject, $body);
}

function cde_tasks_run(string $taskId): void
{
    $task = cde_tasks_get($taskId);
    if ($task === null || (string) ($task['status'] ?? '') !== 'processing') {
        return;
    }

    $userId = (string) ($task['user_id'] ?? '');
    $accountId = trim((string) ($task['account_id'] ?? ''));
    if ($accountId === '' || !cde_salesnav_is_account_alive($accountId)) {
        $resolved = cde_salesnav_resolve_linked_account_id($userId);
        if ($resolved !== null) {
            $accountId = $resolved;
            cde_tasks_update($taskId, ['account_id' => $accountId]);
        }
    }
    if ($accountId === '') {
        $linked = cde_salesnav_session_account();
        if ($linked === null) {
            cde_tasks_update($taskId, [
                'status' => 'failed',
                'error' => 'LinkedIn not connected.',
                'completed_at' => gmdate('c'),
            ]);
            cde_tasks_notify_failed($task, $taskId, 'LinkedIn not connected.');
            return;
        }
        $accountId = (string) $linked['account_id'];
    }

    $creditsCharged = 0;
    $exportRef = 'export:' . $taskId;

    try {
        $config = cde_unipile_api_config($accountId);
        $sourceUrl = (string) ($task['source_url'] ?? '');
        $mode = (string) ($task['mode'] ?? 'list');
        $limit = (int) ($task['limit'] ?? 25);
        $tiers = is_array($task['tiers'] ?? null) ? $task['tiers'] : ['basic' => true, 'enriched' => false, 'mail' => false];

        cde_enforce_salesnav_rate_limits($limit);

        if (cde_credits_billing_enabled()) {
            $storedCount = (int) ($task['source_profile_count'] ?? 0);
            $preflight = cde_tasks_credit_preflight(
                $limit,
                $tiers,
                $userId,
                $storedCount > 0 ? $storedCount : null
            );
            if ($preflight !== null) {
                throw new RuntimeException($preflight['error']);
            }
        }

        $rawRows = cde_salesnav_export($config, $sourceUrl, $mode, $limit);
        $rows = [];
        foreach ($rawRows as $item) {
            if (is_array($item)) {
                $rows[] = cde_salesnav_flatten_lead($item);
            }
        }

        if ($rows === []) {
            throw new RuntimeException('No leads returned. Check the URL and Sales Navigator access.');
        }

        if (!empty($tiers['enriched'])) {
            if (!cde_harvest_enabled()) {
                throw new RuntimeException('Enriched export is temporarily unavailable.');
            }
            $rows = cde_harvest_enrich_rows($rows);
        }

        if (!empty($tiers['mail'])) {
            if (!cde_icypeas_enabled()) {
                throw new RuntimeException('Mail export is temporarily unavailable.');
            }
            $rows = cde_icypeas_enrich_rows($rows);
        }

        $creditCost = cde_credits_export_cost($rows, $tiers);
        if (cde_credits_billing_enabled()) {
            $balance = cde_credits_get_balance($userId);
            if ($balance < $creditCost) {
                throw new RuntimeException(
                    cde_credits_insufficient_export_message(count($rows), $creditCost, $balance)
                );
            }
        }

        cde_tasks_write_csv($taskId, $rows, $tiers);

        if (!cde_credits_consume($userId, $creditCost, $exportRef, [
            'task_id' => $taskId,
            'count' => count($rows),
            'credit_cost' => $creditCost,
        ])) {
            $balance = cde_credits_get_balance($userId);
            throw new RuntimeException(
                cde_credits_insufficient_export_message(count($rows), $creditCost, $balance)
            );
        }
        $creditsCharged = $creditCost;

        $emailsFound = 0;
        if (!empty($tiers['mail'])) {
            foreach ($rows as $row) {
                if (trim((string) ($row['work_email'] ?? '')) !== '') {
                    $emailsFound++;
                }
            }
        }
        $done = [
            'status' => 'ready',
            'lead_count' => count($rows),
            'credits_used' => $creditCost,
            'emails_found' => $emailsFound,
            'completed_at' => gmdate('c'),
            'error' => '',
        ];
        cde_tasks_update($taskId, $done);
        $task = array_merge($task, $done);
        cde_tasks_notify_ready($task, $taskId);
    } catch (Throwable $e) {
        $msg = $e->getMessage();
        $isCreditError = str_starts_with($msg, 'Insufficient export credits');
        if (
            !$isCreditError
            && (
                $msg === cde_salesnav_stale_account_message()
                || cde_unipile_account_error_is_stale(['status' => 0, 'error' => $msg])
            )
        ) {
            cde_salesnav_mark_account_stale($userId, $msg);
            $msg = cde_salesnav_stale_account_message();
        }
        if ($creditsCharged > 0) {
            cde_credits_refund($userId, $creditsCharged, 'refund:' . $exportRef, [
                'task_id' => $taskId,
                'reason' => $msg,
            ]);
        }
        $csvPath = cde_tasks_csv_path($taskId);
        if (is_file($csvPath)) {
            @unlink($csvPath);
        }
        cde_tasks_update($taskId, [
            'status' => 'failed',
            'error' => $msg,
            'credits_used' => 0,
            'lead_count' => 0,
            'completed_at' => gmdate('c'),
        ]);
        $task['error'] = $msg;
        cde_tasks_notify_failed($task, $taskId, $msg);
    }
}
