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
    $url = trim((string) ($body['url'] ?? ''));
    if ($url === '') {
        http_response_code(400);
        echo json_encode(['error' => 'missing_url']);
        exit;
    }
    if (!preg_match('#^https://(docs\.google\.com|drive\.google\.com)#i', $url)) {
        http_response_code(400);
        echo json_encode(['error' => 'invalid_url']);
        exit;
    }

    $fetchUrl = $url;
    if (str_contains($url, '/edit')) {
        $fetchUrl = preg_replace('#/edit.*#', '/export?format=csv', $url) ?? $url;
    }
    if (!str_contains($fetchUrl, 'format=csv') && !str_contains($fetchUrl, 'output=csv')) {
        if (str_contains($fetchUrl, 'pub?')) {
            $fetchUrl .= '&output=csv';
        }
    }

    $ctx = stream_context_create([
        'http' => [
            'timeout' => 20,
            'follow_location' => 1,
            'header' => "User-Agent: HomeFinance/1.0\r\n",
        ],
    ]);
    $csv = @file_get_contents($fetchUrl, false, $ctx);
    if ($csv === false || $csv === '') {
        http_response_code(502);
        echo json_encode(['error' => 'fetch_failed', 'hint' => 'Publica la hoja como CSV o usa export?format=csv']);
        exit;
    }

    $lines = preg_split('/\r\n|\n|\r/', trim($csv)) ?: [];
    if (count($lines) < 2) {
        http_response_code(400);
        echo json_encode(['error' => 'empty_sheet']);
        exit;
    }

    $delimiter = str_contains($lines[0], ';') ? ';' : ',';
    $header = str_getcsv($lines[0], $delimiter);
    $rows = [];
    for ($i = 1; $i < count($lines); $i++) {
        if (trim($lines[$i]) === '') {
            continue;
        }
        $cols = str_getcsv($lines[$i], $delimiter);
        $assoc = [];
        foreach ($header as $hi => $name) {
            $assoc[trim($name)] = $cols[$hi] ?? '';
        }
        $rows[] = $assoc;
    }

    echo json_encode(['ok' => true, 'rows' => $rows, 'headers' => $header]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'server_error']);
}
