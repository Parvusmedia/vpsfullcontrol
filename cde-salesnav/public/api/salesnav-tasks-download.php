<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_customers.php';
require __DIR__ . '/_tasks.php';

$taskId = trim((string) ($_GET['id'] ?? ''));
if ($taskId === '') {
    http_response_code(400);
    echo 'Missing task id';
    exit;
}

$userId = cde_salesnav_user_id();
$task = cde_tasks_get($taskId, $userId);
if ($task === null) {
    http_response_code(404);
    echo 'Task not found';
    exit;
}

if ((string) ($task['status'] ?? '') !== 'ready') {
    http_response_code(409);
    echo 'Export not ready yet';
    exit;
}

$path = cde_tasks_csv_path($taskId);
if (!is_readable($path)) {
    http_response_code(404);
    echo 'File not found';
    exit;
}

$label = preg_replace('/[^a-zA-Z0-9_\-]/', '-', (string) ($task['source_label'] ?? 'export'));
$filename = 'salesnav-' . $label . '-' . $taskId . '.csv';

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Cache-Control: no-store');
readfile($path);
