<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_unipile.php';
require __DIR__ . '/_credits.php';
require __DIR__ . '/_harvest.php';

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

$tiers = cde_credits_parse_tiers($payload);
if (!empty($tiers['enriched'])) {
    if (!cde_harvest_enabled()) {
        cde_json_response(503, [
            'ok' => false,
            'error' => 'Enriched export is temporarily unavailable. Try Basic export or contact support.',
        ]);
    }
    $rows = cde_harvest_enrich_rows($rows);
}

$exportCount = count($rows);
$creditCost = cde_credits_export_cost($rows, $tiers);
$userId = cde_salesnav_user_id();

if (cde_credits_billing_enabled() && cde_credits_get_balance($userId) < $creditCost) {
    cde_json_response(402, [
        'ok' => false,
        'needs_payment' => true,
        'error' => 'Insufficient export credits for this download.',
        'balance' => cde_credits_get_balance($userId),
        'required' => $creditCost,
        'lead_count' => $exportCount,
        'tiers' => $tiers,
    ]);
}

if (!cde_credits_consume($userId, $creditCost, 'export:' . substr(hash('sha256', $sourceUrl . '|' . $exportCount . '|' . gmdate('Y-m-d-H-i')), 0, 16), [
    'mode' => $mode,
    'limit' => $limit,
    'count' => $exportCount,
    'credit_cost' => $creditCost,
    'tiers' => $tiers,
])) {
    cde_json_response(402, [
        'ok' => false,
        'needs_payment' => true,
        'error' => 'Insufficient export credits for this download.',
        'balance' => cde_credits_get_balance($userId),
        'required' => $creditCost,
        'lead_count' => $exportCount,
        'tiers' => $tiers,
    ]);
}

$seconds = max(1, (int) round(microtime(true) - $started));

$enrichedCount = 0;
if (!empty($tiers['enriched'])) {
    foreach ($rows as $row) {
        if (trim((string) ($row['company_domain'] ?? '')) !== '' || trim((string) ($row['profile_summary'] ?? '')) !== '') {
            $enrichedCount++;
        }
    }
}

cde_json_response(200, [
    'ok' => true,
    'count' => count($rows),
    'limit' => $limit,
    'mode' => $mode,
    'seconds' => $seconds,
    'rows' => $rows,
    'preview' => array_slice($rows, 0, 10),
    'credits_used' => $creditCost,
    'tiers' => $tiers,
    'balance' => cde_credits_get_balance($userId),
    'enriched_count' => $enrichedCount,
]);
