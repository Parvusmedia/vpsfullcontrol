<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_unipile.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
}

cde_enforce_bot_guards($payload);

$listUrl = trim((string) ($payload['list_url'] ?? ''));
$searchUrl = trim((string) ($payload['search_url'] ?? ''));
$limit = (int) ($payload['limit'] ?? 25);

if ($limit < 1) {
    $limit = 25;
}
if ($limit > 2000) {
    $limit = 2000;
}

cde_enforce_salesnav_rate_limits($limit);

$linked = cde_salesnav_require_account();
$config = cde_unipile_api_config($linked['account_id']);
$sourceUrl = '';
if ($listUrl !== '') {
    $sourceUrl = cde_salesnav_normalize_list_url($listUrl);
    $mode = 'list';
} elseif ($searchUrl !== '') {
    $sourceUrl = cde_salesnav_normalize_search_url($searchUrl);
    $mode = 'search';
} else {
    cde_json_response(400, [
        'ok' => false,
        'error' => 'Provide a Sales Navigator list URL or search URL.',
    ]);
}

$started = microtime(true);
$rawRows = cde_salesnav_export($config, $sourceUrl, $mode, $limit);
$rows = [];
foreach ($rawRows as $item) {
    if (is_array($item)) {
        $rows[] = cde_salesnav_flatten_lead($item);
    }
}

if ($rows === []) {
    cde_json_response(404, [
        'ok' => false,
        'error' => 'No leads returned. Check the URL and that your LinkedIn account has access to this list.',
    ]);
}

$seconds = max(1, (int) round(microtime(true) - $started));

cde_json_response(200, [
    'ok' => true,
    'count' => count($rows),
    'limit' => $limit,
    'mode' => $mode,
    'seconds' => $seconds,
    'rows' => $rows,
    'preview' => array_slice($rows, 0, 10),
]);
