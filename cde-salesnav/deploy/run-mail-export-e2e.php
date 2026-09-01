#!/usr/bin/env php
<?php
declare(strict_types=1);
$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_unipile.php';
require $docroot . '/api/_tasks.php';
$limit = max(1, min(10, (int) ($argv[1] ?? 5)));
$email = 'emiliano@parvusmedia.com';
$userId = cde_salesnav_user_id_for_email($email);
$accounts = cde_salesnav_load_accounts();
$accountId = '';
foreach ([$userId, '08e41458b464521bd860'] as $uid) {
    $rec = $accounts[$uid] ?? null;
    if (is_array($rec) && !empty($rec['account_id'])) {
        $accountId = (string) $rec['account_id'];
        break;
    }
}
if ($accountId === '') {
    foreach ($accounts as $rec) {
        if (is_array($rec) && !empty($rec['account_id'])) {
            $accountId = (string) $rec['account_id'];
            break;
        }
    }
}
if ($accountId === '') { fwrite(STDERR, "No LinkedIn account_id\n"); exit(1); }
$listUrl = 'https://www.linkedin.com/sales/lists/people/7429481205567352833';
$taskId = cde_tasks_new_id();
$task = [
    'user_id' => $userId, 'email' => $email, 'account_id' => $accountId,
    'status' => 'processing', 'mode' => 'list',
    'source_url' => cde_salesnav_normalize_list_url($listUrl),
    'source_label' => 'List 7429481205567352833', 'limit' => $limit,
    'limit_label' => (string) $limit,
    'tiers' => ['basic' => true, 'enriched' => true, 'mail' => true],
    'lead_count' => 0, 'credits_used' => 0, 'error' => '',
    'created_at' => gmdate('c'), 'started_at' => gmdate('c'), 'completed_at' => '',
];
$all = cde_tasks_load_all();
$all[$taskId] = $task;
cde_tasks_save_all($all);
echo "task_id={$taskId}\nuser={$email} balance_before=" . cde_credits_get_balance($userId) . "\n";
echo "account_id={$accountId}\nlimit={$limit} tiers=enriched+mail\nrunning...\n";
$started = microtime(true);
cde_tasks_run($taskId);
$elapsed = round(microtime(true) - $started, 1);
$done = cde_tasks_get($taskId) ?? [];
$status = (string) ($done['status'] ?? 'unknown');
echo "status={$status} elapsed={$elapsed}s\n";
echo "lead_count=" . (int)($done['lead_count'] ?? 0) . " emails_found=" . (int)($done['emails_found'] ?? 0) . "\n";
echo "credits_used=" . (int)($done['credits_used'] ?? 0) . " balance_after=" . cde_credits_get_balance($userId) . "\n";
if (!empty($done['error'])) echo "error=" . $done['error'] . "\n";
$csvPath = cde_tasks_csv_path($taskId);
if (!is_readable($csvPath)) { echo "csv=missing\n"; exit($status === 'ready' ? 1 : 2); }
$lines = file($csvPath, FILE_IGNORE_NEW_LINES);
echo "csv_header=" . ($lines[0] ?? '') . "\n";
$header = str_getcsv((string)($lines[0] ?? ''));
$mailIdx = array_search('work_email', $header, true);
$withEmail = 0;
foreach (array_slice($lines, 1) as $line) {
    $cells = str_getcsv($line);
    $we = trim((string)($cells[$mailIdx !== false ? $mailIdx : -1] ?? ''));
    if ($we !== '') { $withEmail++; echo "sample_email={$we}\n"; }
}
echo "csv_emails_non_empty={$withEmail}\n";
exit($status === 'ready' && $withEmail > 0 ? 0 : ($status === 'ready' ? 3 : 4));
