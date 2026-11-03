<?php

declare(strict_types=1);

require_once __DIR__ . '/_publora.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body.']);
}

$activityId = trim((string) ($input['activityId'] ?? ''));
$platformId = trim((string) ($input['platformId'] ?? ''));
$action = trim((string) ($input['action'] ?? ''));

if ($activityId === '' || $platformId === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'activityId and platformId required.']);
}

if (!in_array($action, ['approve', 'decline'], true)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'action must be approve or decline.']);
}

$store = gaggle_demo_read_json_file('activities.json', ['activities' => []]);
$activities = $store['activities'] ?? [];
$idx = null;
$activity = null;
foreach ($activities as $i => $row) {
    if (is_array($row) && ($row['id'] ?? '') === $activityId) {
        $idx = $i;
        $activity = $row;
        break;
    }
}

if ($activity === null || ($activity['status'] ?? '') !== 'open') {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Activity not found or already closed.']);
}

$targets = $activity['targetPlatformIds'] ?? [];
if (is_array($targets) && $targets !== [] && !in_array($platformId, $targets, true)) {
    gaggle_demo_json_response(403, ['ok' => false, 'error' => 'This account is not in the activity audience.']);
}

$responses = gaggle_demo_read_json_file('responses.json', ['responses' => []]);
$responseList = $responses['responses'] ?? [];
if (!is_array($responseList)) {
    $responseList = [];
}

foreach ($responseList as $r) {
    if (is_array($r) && ($r['activityId'] ?? '') === $activityId && ($r['platformId'] ?? '') === $platformId) {
        gaggle_demo_json_response(409, ['ok' => false, 'error' => 'Already responded for this activity and account.']);
    }
}

$record = [
    'activityId' => $activityId,
    'platformId' => $platformId,
    'action' => $action,
    'completedAt' => gmdate('c'),
    'postGroupId' => null,
];

if ($action === 'approve') {
    $pub = gaggle_publora_publish_activity($activity, $platformId);
    if (!$pub['ok']) {
        gaggle_demo_json_response(502, ['ok' => false, 'error' => $pub['error'] ?? 'Publish failed', 'detail' => $pub['body'] ?? null]);
    }
    $record['postGroupId'] = $pub['postGroupId'] ?? null;
}

$responseList[] = $record;

$approvedCount = 0;
$declinedCount = 0;
foreach ($responseList as $r) {
    if (!is_array($r) || ($r['activityId'] ?? '') !== $activityId) {
        continue;
    }
    if (($r['action'] ?? '') === 'approve') {
        $approvedCount++;
    }
    if (($r['action'] ?? '') === 'decline') {
        $declinedCount++;
    }
}

$targetCount = is_array($targets) && $targets !== [] ? count($targets) : 0;
if ($targetCount > 0 && ($approvedCount + $declinedCount) >= $targetCount) {
    $activities[$idx]['status'] = 'closed';
    $activities[$idx]['closedAt'] = gmdate('c');
}

gaggle_demo_write_json_file('responses.json', ['responses' => $responseList]);
gaggle_demo_write_json_file('activities.json', ['activities' => $activities]);

gaggle_demo_json_response(200, [
    'ok' => true,
    'response' => $record,
    'activityStatus' => $activities[$idx]['status'] ?? 'open',
]);
