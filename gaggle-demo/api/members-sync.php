<?php

declare(strict_types=1);

require_once __DIR__ . '/_connect.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_full_admin();
$input = json_decode((string) file_get_contents('php://input'), true);
$memberId = trim((string) ($input['memberId'] ?? ''));
if ($memberId === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'memberId required']);
}

$result = ngaged_sync_member_linkedin($memberId);
if (!$result['ok']) {
    gaggle_demo_json_response(422, ['ok' => false, 'error' => $result['error'] ?? 'Sync failed']);
}

gaggle_demo_json_response(200, ['ok' => true, 'member' => $result['member'] ?? null, 'platformId' => $result['platformId'] ?? null]);
