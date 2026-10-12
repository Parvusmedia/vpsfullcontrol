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
    $body = hf_json_body();
    $forceAll = !empty($body['force_all']);
    $month = isset($body['month']) ? (string) $body['month'] : '';

    $store = hf_read_store();
    $updated = 0;

    foreach ($store['transactions'] as $i => $tx) {
        if (!is_array($tx)) {
            continue;
        }
        if ($month !== '' && preg_match('/^\d{4}-\d{2}$/', $month) && ($tx['month'] ?? '') !== $month) {
            continue;
        }
        $cat = (string) ($tx['category'] ?? '');
        if (!$forceAll && $cat !== '' && $cat !== 'Otros') {
            continue;
        }
        $copy = $tx;
        $copy['category'] = '';
        $copy = hf_apply_rules($copy, $store['rules']);
        if (($copy['category'] ?? '') === '') {
            $copy['category'] = 'Otros';
        }
        if ($copy['category'] !== $cat || ($copy['tags'] ?? []) !== ($tx['tags'] ?? [])) {
            $store['transactions'][$i]['category'] = $copy['category'];
            if (!empty($copy['tags'])) {
                $store['transactions'][$i]['tags'] = $copy['tags'];
            }
            $updated++;
        }
    }

    hf_write_store($store);
    echo json_encode(['ok' => true, 'updated' => $updated]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'server_error']);
}
