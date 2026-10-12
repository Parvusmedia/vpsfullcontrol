<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';

hf_require_auth();

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'method_not_allowed']);
    exit;
}

try {
    $store = hf_read_store();
    $removed = hf_clean_matrix_duplicates($store);
    if ($removed > 0) {
        hf_write_store($store);
    }
    echo json_encode([
        'ok' => true,
        'removed' => $removed,
        'total' => count($store['transactions']),
    ]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'server_error']);
}
