<?php
declare(strict_types=1);

require_once __DIR__ . '/_customers.php';
require_once __DIR__ . '/_tasks.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

if (cde_salesnav_session_email() === null) {
    cde_json_response(401, ['ok' => false, 'error' => 'Sign in with your work email first.']);
}

$linked = cde_salesnav_require_valid_account();

$listUrl = trim((string) ($_GET['list_url'] ?? ''));
$searchUrl = trim((string) ($_GET['search_url'] ?? ''));
$mode = trim((string) ($_GET['mode'] ?? ''));

if ($listUrl !== '') {
    $sourceUrl = cde_salesnav_normalize_list_url($listUrl);
    $mode = 'list';
} elseif ($searchUrl !== '') {
    $sourceUrl = cde_salesnav_normalize_search_url($searchUrl);
    $mode = 'search';
} else {
    cde_json_response(400, ['ok' => false, 'error' => 'Provide list_url or search_url.']);
}

$accountId = trim((string) ($linked['account_id'] ?? ''));
$config = cde_unipile_api_config($accountId);
$meta = cde_salesnav_probe_source_meta($config, $sourceUrl, $mode);
$sourceName = cde_tasks_normalize_export_name((string) ($meta['source_name'] ?? ''));

if ($sourceName === '') {
    $sourceName = cde_tasks_default_source_label($sourceUrl, $mode);
}

cde_json_response(200, [
    'ok' => true,
    'mode' => $mode,
    'source_name' => $sourceName,
    'profile_count' => $meta['profile_count'],
]);
