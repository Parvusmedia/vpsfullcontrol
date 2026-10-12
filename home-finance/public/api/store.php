<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';

hf_require_auth();

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

try {
    if ($method === 'GET') {
        $store = hf_read_store();
        echo json_encode([
            'categories' => $store['categories'],
            'rules' => $store['rules'],
            'budgets' => $store['budgets'] ?? [],
            'fixed_categories' => $store['fixed_categories'] ?? [],
            'transaction_count' => count($store['transactions']),
        ]);
        exit;
    }

    if ($method === 'PUT') {
        $body = hf_json_body();
        $store = hf_read_store();
        if (isset($body['categories']) && is_array($body['categories'])) {
            $store['categories'] = array_values(array_filter(array_map('strval', $body['categories'])));
        }
        if (isset($body['rules']) && is_array($body['rules'])) {
            $store['rules'] = $body['rules'];
        }
        if (isset($body['budgets']) && is_array($body['budgets'])) {
            $store['budgets'] = $body['budgets'];
        }
        if (isset($body['fixed_categories']) && is_array($body['fixed_categories'])) {
            $store['fixed_categories'] = array_values(array_map('strval', $body['fixed_categories']));
        }
        hf_write_store($store);
        echo json_encode(['ok' => true]);
        exit;
    }

    http_response_code(405);
    echo json_encode(['error' => 'method_not_allowed']);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'server_error']);
}
