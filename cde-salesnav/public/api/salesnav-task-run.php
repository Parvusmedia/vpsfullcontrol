#!/usr/bin/env php
<?php
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    echo 'CLI only';
    exit(1);
}

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_tasks.php';

$taskId = trim((string) ($argv[1] ?? ''));
if ($taskId === '') {
    fwrite(STDERR, "Usage: salesnav-task-run.php <task_id>\n");
    exit(1);
}

set_time_limit(0);
ignore_user_abort(true);

cde_tasks_run($taskId);

$task = cde_tasks_get($taskId);
$status = is_array($task) ? (string) ($task['status'] ?? '') : 'missing';
fwrite(STDOUT, $taskId . ' ' . $status . "\n");
exit($status === 'ready' ? 0 : 1);
