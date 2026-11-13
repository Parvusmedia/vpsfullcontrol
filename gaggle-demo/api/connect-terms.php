<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_legal.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'GET only']);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'terms' => ngaged_terms_acceptance_meta(),
]);
