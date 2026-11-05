<?php

declare(strict_types=1);

require_once __DIR__ . '/_stats.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

gaggle_demo_require_admin();

$daysParam = trim((string) ($_GET['days'] ?? '30'));
$days = $daysParam === 'all' ? 0 : max(1, min(365, (int) $daysParam));

$stats = ngaged_compute_stats($days);
gaggle_demo_json_response(200, ['ok' => true] + $stats);
