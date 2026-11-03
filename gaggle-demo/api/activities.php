<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

gaggle_demo_cors();

$method = $_SERVER['REQUEST_METHOD'];
$store = gaggle_demo_read_json_file('activities.json', ['activities' => []]);
$activities = $store['activities'] ?? [];
if (!is_array($activities)) {
    $activities = [];
}

if ($method === 'GET') {
    $open = array_values(array_filter($activities, static function ($a) {
        return is_array($a) && ($a['status'] ?? '') === 'open';
    }));
    usort($open, static fn ($a, $b) => strcmp((string) ($b['createdAt'] ?? ''), (string) ($a['createdAt'] ?? '')));
    gaggle_demo_json_response(200, ['ok' => true, 'activities' => $open]);
}

if ($method === 'POST') {
    gaggle_demo_require_admin();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body.']);
    }

    $type = (string) ($input['type'] ?? 'post');
    if (!in_array($type, ['post', 'repost'], true)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'type must be post or repost.']);
    }

    $title = trim((string) ($input['title'] ?? ''));
    if ($title === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'title is required.']);
    }

    $targetIds = $input['targetPlatformIds'] ?? [];
    if (!is_array($targetIds)) {
        $targetIds = [];
    }
    $targetIds = array_values(array_unique(array_filter(array_map('strval', $targetIds))));

    $activity = [
        'id' => gaggle_demo_new_id('act'),
        'title' => $title,
        'type' => $type,
        'content' => trim((string) ($input['content'] ?? '')),
        'repostParentUrn' => trim((string) ($input['repostParentUrn'] ?? '')),
        'targetPlatformIds' => $targetIds,
        'createdAt' => gmdate('c'),
        'status' => 'open',
    ];

    if ($type === 'repost' && $activity['repostParentUrn'] === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'repostParentUrn required for repost.']);
    }

    $activities[] = $activity;
    gaggle_demo_write_json_file('activities.json', ['activities' => $activities]);
    gaggle_demo_json_response(201, ['ok' => true, 'activity' => $activity]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
