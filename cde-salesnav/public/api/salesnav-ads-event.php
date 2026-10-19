<?php
declare(strict_types=1);

/**
 * Mirror browser OpenAI Ads events via Conversions API (same event_id as pixel for dedup).
 * Used for landing contents_viewed from /salesnav/.
 */

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_openai_ads.php';

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
    $payload = [];
}

$type = trim((string) ($payload['type'] ?? ''));
$eventId = trim((string) ($payload['event_id'] ?? ''));
$sourceUrl = trim((string) ($payload['source_url'] ?? ''));

if ($type !== 'contents_viewed') {
    cde_json_response(400, ['ok' => false, 'error' => 'Unsupported event type']);
}

if ($eventId === '' || !preg_match('/^landing_[0-9]+_[a-z0-9]{6,16}$/', $eventId)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid event_id']);
}

$landing = cde_openai_ads_landing_source_url();
if ($sourceUrl !== '' && !str_starts_with($sourceUrl, $landing)) {
    cde_json_response(400, ['ok' => false, 'error' => 'Invalid source_url']);
}

$sent = cde_openai_ads_track_contents_viewed($eventId, $sourceUrl !== '' ? $sourceUrl : $landing);

cde_json_response(200, [
    'ok' => true,
    'sent' => $sent,
    'duplicate' => !$sent && cde_openai_ads_already_sent($eventId),
]);
