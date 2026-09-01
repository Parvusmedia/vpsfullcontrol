<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_tasks.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

$userId = cde_salesnav_user_id();
$email = cde_salesnav_session_email() ?? '';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    cde_json_response(200, [
        'ok' => true,
        'tasks' => cde_tasks_for_user($userId),
    ]);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

if ($email === '') {
    cde_json_response(401, ['ok' => false, 'error' => 'Sign in with your work email first.']);
}

$linked = cde_salesnav_require_valid_account();

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
}

cde_enforce_bot_guards($payload);

$created = cde_tasks_create($userId, $email, $payload);
$taskId = (string) $created['task_id'];
$task = $created['task'];

cde_tasks_notify_started($task, $taskId);

$view = cde_tasks_public_view(array_merge($task, ['id' => $taskId]));

http_response_code(202);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
echo json_encode([
    'ok' => true,
    'task' => $view,
    'message' => 'processing',
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

if (function_exists('fastcgi_finish_request')) {
    fastcgi_finish_request();
} elseif (ob_get_level() > 0) {
    @ob_end_flush();
    @flush();
}

if (!cde_tasks_spawn_run($taskId)) {
    ignore_user_abort(true);
    set_time_limit(0);
    cde_tasks_run($taskId);
}
exit;
