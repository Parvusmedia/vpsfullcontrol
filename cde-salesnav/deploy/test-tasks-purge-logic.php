<?php
/**
 * Standalone logic test for task delete/purge helpers (no bootstrap).
 * Run on a host with PHP: php deploy/test-tasks-purge-logic.php
 */
declare(strict_types=1);

const CDE_TASKS_RETENTION_DAYS = 90;

function cde_tasks_is_deletable(array $task): bool
{
    $status = (string) ($task['status'] ?? '');
    return $status === 'ready' || $status === 'failed';
}

function cde_tasks_reference_timestamp(array $task): int
{
    $raw = (string) ($task['completed_at'] ?? $task['created_at'] ?? '');
    $ts = strtotime($raw);
    return $ts !== false ? $ts : 0;
}

function cde_tasks_purge_expired(array &$all, int $days = CDE_TASKS_RETENTION_DAYS): int
{
    $cutoff = time() - ($days * 86400);
    $removed = 0;
    foreach ($all as $taskId => $task) {
        if (!is_array($task) || !cde_tasks_is_deletable($task)) {
            continue;
        }
        if (cde_tasks_reference_timestamp($task) >= $cutoff) {
            continue;
        }
        unset($all[$taskId]);
        $removed++;
    }
    return $removed;
}

$old = gmdate('c', time() - (91 * 86400));
$recent = gmdate('c', time() - (10 * 86400));

$all = [
    'tsk_old_ready' => ['status' => 'ready', 'completed_at' => $old],
    'tsk_old_failed' => ['status' => 'failed', 'completed_at' => $old],
    'tsk_new_ready' => ['status' => 'ready', 'completed_at' => $recent],
    'tsk_processing' => ['status' => 'processing', 'created_at' => $old],
];

$removed = cde_tasks_purge_expired($all);
assert($removed === 2, 'should purge 2 old tasks');
assert(!isset($all['tsk_old_ready']) && !isset($all['tsk_old_failed']), 'old tasks gone');
assert(isset($all['tsk_new_ready']) && isset($all['tsk_processing']), 'recent + processing kept');

assert(!cde_tasks_is_deletable(['status' => 'processing']), 'processing not deletable');
assert(cde_tasks_is_deletable(['status' => 'ready']), 'ready deletable');

fwrite(STDOUT, "OK purge logic tests passed\n");
