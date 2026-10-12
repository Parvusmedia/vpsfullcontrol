<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';

hf_require_auth();

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

try {
    if ($method === 'GET') {
        $store = hf_read_store();
        $month = isset($_GET['month']) ? (string) $_GET['month'] : '';
        $txs = $store['transactions'];
        if ($month !== '' && preg_match('/^\d{4}-\d{2}$/', $month)) {
            $txs = array_values(array_filter($txs, static function ($t) use ($month) {
                return is_array($t) && ($t['month'] ?? '') === $month;
            }));
        }
        echo json_encode(['transactions' => $txs]);
        exit;
    }

    if ($method === 'PATCH') {
        $body = hf_json_body();
        $id = (string) ($body['id'] ?? '');
        if ($id === '') {
            http_response_code(400);
            echo json_encode(['error' => 'missing_id']);
            exit;
        }
        $store = hf_read_store();
        $found = false;
        foreach ($store['transactions'] as $i => $tx) {
            if (!is_array($tx) || ($tx['id'] ?? '') !== $id) {
                continue;
            }
            if (isset($body['category'])) {
                $store['transactions'][$i]['category'] = (string) $body['category'];
            }
            if (isset($body['tags']) && is_array($body['tags'])) {
                $store['transactions'][$i]['tags'] = array_values(array_map('strval', $body['tags']));
            }
            if (isset($body['type'])) {
                $store['transactions'][$i]['type'] = (string) $body['type'];
            }
            if (isset($body['save_rule']) && $body['save_rule'] === true) {
                $pattern = (string) ($body['rule_pattern'] ?? '');
                if ($pattern === '' && isset($store['transactions'][$i]['concept'])) {
                    $words = preg_split('/\s+/', hf_normalize_concept((string) $store['transactions'][$i]['concept'])) ?: [];
                    $pattern = $words[0] ?? '';
                }
                if ($pattern !== '') {
                    $store['rules'][] = [
                        'pattern' => $pattern,
                        'category' => (string) ($store['transactions'][$i]['category'] ?? 'Otros'),
                        'tags' => $store['transactions'][$i]['tags'] ?? [],
                    ];
                }
            }
            $found = true;
            break;
        }
        if (!$found) {
            http_response_code(404);
            echo json_encode(['error' => 'not_found']);
            exit;
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
