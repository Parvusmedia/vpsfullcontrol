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
    $rows = $body['rows'] ?? null;
    if (!is_array($rows)) {
        http_response_code(400);
        echo json_encode(['error' => 'missing_rows']);
        exit;
    }

    $store = hf_read_store();
    $existingIds = [];
    foreach ($store['transactions'] as $tx) {
        if (is_array($tx) && isset($tx['id'])) {
            $existingIds[(string) $tx['id']] = true;
        }
    }

    $added = 0;
    $skipped = 0;

    foreach ($rows as $row) {
        if (!is_array($row)) {
            continue;
        }
        $date = (string) ($row['date'] ?? '');
        $concept = trim((string) ($row['concept'] ?? ''));
        $amount = (float) ($row['amount'] ?? 0);
        if ($date === '' || $concept === '') {
            continue;
        }
        $account = trim((string) ($row['account'] ?? ''));
        $type = (string) ($row['type'] ?? '');
        if ($type === '') {
            $conceptLower = function_exists('mb_strtolower') ? mb_strtolower($concept, 'UTF-8') : strtolower($concept);
            if (preg_match('/traspaso|transferencia entre/i', $conceptLower)) {
                $type = 'transferencia';
            } else {
                $type = $amount >= 0 ? 'ingreso' : 'gasto';
            }
        }
        $category = trim((string) ($row['category'] ?? ''));
        $tags = $row['tags'] ?? [];
        if (!is_array($tags)) {
            $tags = [];
        }

        $tx = [
            'date' => $date,
            'concept' => $concept,
            'amount' => $amount,
            'account' => $account,
            'type' => $type,
            'category' => $category,
            'tags' => array_values(array_map('strval', $tags)),
            'month' => hf_month_key($date),
        ];
        $tx = hf_apply_rules($tx, $store['rules']);
        $id = hf_tx_id($tx);
        if (isset($existingIds[$id])) {
            $skipped++;
            continue;
        }
        $tx['id'] = $id;
        $store['transactions'][] = $tx;
        $existingIds[$id] = true;
        $added++;
    }

    hf_write_store($store);
    echo json_encode([
        'ok' => true,
        'added' => $added,
        'skipped' => $skipped,
        'total' => count($store['transactions']),
    ]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'server_error']);
}
