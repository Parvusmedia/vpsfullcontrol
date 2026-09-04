#!/usr/bin/env php
<?php
/**
 * Purge completed/failed Sales Nav export tasks older than retention (default 90 days).
 *
 * Usage:
 *   php purge-salesnav-tasks.php [--days=90] [--dry-run]
 *
 * Cron (daily on production):
 *   15 4 * * * /opt/plesk/php/8.3/bin/php /var/www/vhosts/companydataenrichment.com/httpdocs/../deploy/purge-salesnav-tasks.php >> /var/www/vhosts/companydataenrichment.com/private/cde/salesnav_task_purge.log 2>&1
 */
declare(strict_types=1);

$days = 90;
$dryRun = false;

foreach (array_slice($argv, 1) as $arg) {
    if ($arg === '--dry-run') {
        $dryRun = true;
        continue;
    }
    if (str_starts_with($arg, '--days=')) {
        $days = max(1, (int) substr($arg, strlen('--days=')));
    }
}

$docroot = '/var/www/vhosts/companydataenrichment.com/httpdocs';
if (!is_dir($docroot)) {
    $docroot = dirname(__DIR__) . '/public';
}

require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_tasks.php';

if ($dryRun) {
    $cutoff = time() - ($days * 86400);
    $all = cde_tasks_load_all();
    $wouldRemove = 0;
    foreach ($all as $taskId => $task) {
        if (!is_array($task) || !cde_tasks_is_deletable($task)) {
            continue;
        }
        if (cde_tasks_reference_timestamp($task) >= $cutoff) {
            continue;
        }
        $wouldRemove++;
        fwrite(STDOUT, "would purge {$taskId} status=" . ($task['status'] ?? '') . "\n");
    }
    fwrite(STDOUT, "Dry run: {$wouldRemove} task(s) older than {$days} day(s).\n");
    exit(0);
}

$removed = cde_tasks_purge_expired($days);
fwrite(STDOUT, gmdate('c') . " purged {$removed} task(s) older than {$days} day(s).\n");
