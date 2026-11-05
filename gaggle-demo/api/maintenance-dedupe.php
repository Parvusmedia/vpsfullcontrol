<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_members_util.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_full_admin();

$store = ngaged_members_store();
$result = ngaged_deduplicate_members_store($store);
ngaged_save_members($result['store']);

gaggle_demo_json_response(200, [
    'ok' => true,
    'removed' => $result['removed'],
    'members' => count($result['store']['members'] ?? []),
]);
