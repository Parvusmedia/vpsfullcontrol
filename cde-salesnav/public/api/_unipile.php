<?php
/**
 * Unipile helpers for Sales Navigator export (NavExport simple tier).
 */

declare(strict_types=1);

function cde_load_unipile_config(): array
{
    $candidates = [
        dirname(__DIR__, 2) . '/private/cde/unipile.env',
        __DIR__ . '/unipile.env',
    ];

    $env = [];
    foreach ($candidates as $path) {
        if (!is_readable($path)) {
            continue;
        }
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $env[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }

    $apiKey = $env['UNIPILE_API_KEY'] ?? getenv('UNIPILE_API_KEY') ?: '';
    $accountId = $env['UNIPILE_ACCOUNT_ID'] ?? getenv('UNIPILE_ACCOUNT_ID') ?: '';
    $base = $env['UNIPILE_BASE_URL'] ?? getenv('UNIPILE_BASE_URL') ?: 'https://api.unipile.com/v2';
    $base = rtrim(trim($base), '/');

    if ($apiKey === '' || $accountId === '') {
        cde_json_response(500, [
            'ok' => false,
            'error' => 'Server misconfigured: Unipile credentials missing.',
        ]);
    }

    $isV1 = (strpos($base, '/api/v1') !== false)
        || (substr($base, -3) !== '/v2' && strpos($base, 'api.unipile.com/v2') === false);

    return [
        'api_key' => $apiKey,
        'account_id' => $accountId,
        'base' => $base,
        'is_v1' => $isV1,
    ];
}

function cde_salesnav_normalize_list_url(string $value): string
{
    $value = trim($value);
    if (preg_match('#https?://(?:www\.)?linkedin\.com/sales/lists/people/\d+#i', $value, $m)) {
        return $m[0];
    }
    if (ctype_digit($value)) {
        return 'https://www.linkedin.com/sales/lists/people/' . $value;
    }
    cde_json_response(400, [
        'ok' => false,
        'error' => 'Invalid Sales Navigator list URL or list id.',
    ]);
}

function cde_salesnav_normalize_search_url(string $value): string
{
    $value = trim($value);
    if (preg_match('#https?://(?:www\.)?linkedin\.com/sales/search/people#i', $value, $m)) {
        return $value;
    }
    cde_json_response(400, [
        'ok' => false,
        'error' => 'Invalid Sales Navigator search URL.',
    ]);
}

function cde_unipile_request(
    array $config,
    string $method,
    string $path,
    ?array $query = null,
    ?array $body = null,
    int $timeout = 120
): array {
    $url = $config['base'] . $path;
    if ($query) {
        $parts = [];
        foreach ($query as $k => $v) {
            $parts[] = $k === 'cursor'
                ? rawurlencode($k) . '=' . rawurlencode((string) $v)
                : rawurlencode($k) . '=' . rawurlencode((string) $v);
        }
        $url .= '?' . implode('&', $parts);
    }

    $headers = [
        'X-API-KEY: ' . $config['api_key'],
        'Accept: application/json',
    ];

    $ch = curl_init($url);
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => strtoupper($method),
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_CONNECTTIMEOUT => 30,
    ];

    if ($body !== null) {
        $json = json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $headers[] = 'Content-Type: application/json';
        $opts[CURLOPT_HTTPHEADER] = $headers;
        $opts[CURLOPT_POSTFIELDS] = $json;
    }

    curl_setopt_array($ch, $opts);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'status' => 0, 'error' => $err ?: 'Unipile request failed'];
    }

    $data = json_decode((string) $raw, true);
    if (!is_array($data)) {
        $data = [];
    }

    if ($code >= 400) {
        $msg = $data['title'] ?? $data['error'] ?? $data['message'] ?? 'Unipile API error';
        return ['ok' => false, 'status' => $code, 'error' => (string) $msg, 'data' => $data];
    }

    return ['ok' => true, 'status' => $code, 'data' => $data];
}

function cde_salesnav_collect_items(array $page): array
{
    foreach (['items', 'data', 'results', 'leads'] as $key) {
        if (isset($page[$key]) && is_array($page[$key])) {
            return $page[$key];
        }
    }
    return [];
}

function cde_salesnav_flatten_lead(array $item): array
{
    $company = $item['company'] ?? [];
    if (is_string($company)) {
        $company = ['name' => $company];
    }
    if (!is_array($company)) {
        $company = [];
    }

    $positions = $item['current_positions'] ?? $item['positions'] ?? [];
    $role = '';
    $companyName = (string) ($company['name'] ?? $item['company_name'] ?? '');
    if (is_array($positions) && isset($positions[0]) && is_array($positions[0])) {
        $role = (string) ($positions[0]['role'] ?? $positions[0]['title'] ?? '');
        if ($companyName === '') {
            $companyName = (string) ($positions[0]['company'] ?? '');
        }
    }

    $name = (string) ($item['name'] ?? '');
    $parts = $name !== '' ? preg_split('/\s+/', $name, 2) : ['', ''];
    $first = (string) ($item['first_name'] ?? ($parts[0] ?? ''));
    $last = (string) ($item['last_name'] ?? ($parts[1] ?? ''));

    return [
        'first_name' => $first,
        'last_name' => $last,
        'full_name' => $name !== '' ? $name : trim($first . ' ' . $last),
        'job_title' => (string) ($item['headline'] ?? $role ?? $item['title'] ?? ''),
        'company_name' => $companyName,
        'location' => (string) ($item['location'] ?? ''),
        'linkedin_url' => (string) ($item['public_profile_url'] ?? $item['profile_url'] ?? $item['linkedin_url'] ?? ''),
        'sales_nav_id' => (string) ($item['id'] ?? $item['member_id'] ?? ''),
        'open_profile' => (string) ($item['open_profile'] ?? $item['open_link'] ?? ''),
        'connection_degree' => (string) ($item['network_distance'] ?? $item['degree'] ?? ''),
    ];
}

function cde_salesnav_paginate_v1(array $config, string $sourceUrl, int $maxLeads): array
{
    $collected = [];
    $cursor = null;

    while (count($collected) < $maxLeads) {
        $pageSize = min(25, $maxLeads - count($collected));
        $query = [
            'account_id' => $config['account_id'],
            'limit' => $pageSize,
        ];
        if ($cursor !== null) {
            $query['cursor'] = $cursor;
        }

        $resp = cde_unipile_request(
            $config,
            'POST',
            '/linkedin/search',
            $query,
            ['url' => $sourceUrl]
        );
        if (!$resp['ok']) {
            cde_json_response($resp['status'] >= 400 && $resp['status'] < 600 ? $resp['status'] : 502, [
                'ok' => false,
                'error' => $resp['error'] ?? 'Export failed',
            ]);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $cursor = $resp['data']['cursor'] ?? $resp['data']['next_cursor'] ?? null;
        if ($cursor === null || $cursor === '') {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_paginate_v2_search(array $config, string $searchUrl, int $maxLeads): array
{
    $collected = [];
    $cursor = null;
    $limit = min(100, $maxLeads);

    while (count($collected) < $maxLeads) {
        $query = ['limit' => $limit];
        if ($cursor !== null) {
            $query['cursor'] = $cursor;
        }

        $resp = cde_unipile_request(
            $config,
            'POST',
            '/' . rawurlencode($config['account_id']) . '/linkedin/sales-navigator/search',
            $query,
            ['url' => $searchUrl]
        );
        if (!$resp['ok']) {
            cde_json_response($resp['status'] >= 400 && $resp['status'] < 600 ? $resp['status'] : 502, [
                'ok' => false,
                'error' => $resp['error'] ?? 'Export failed',
            ]);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $cursor = $resp['data']['next_cursor'] ?? $resp['data']['cursor'] ?? null;
        if ($cursor === null || $cursor === '' || count($batch) < $limit) {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_paginate_v2_list(array $config, string $listId, int $maxLeads): array
{
    $collected = [];
    $offset = 0;
    $limit = min(100, $maxLeads);

    while (count($collected) < $maxLeads) {
        $resp = cde_unipile_request(
            $config,
            'POST',
            '/' . rawurlencode($config['account_id']) . '/linkedin/sales-navigator/lead-lists/' . rawurlencode($listId),
            ['limit' => $limit, 'offset' => $offset],
            []
        );
        if (!$resp['ok']) {
            cde_json_response($resp['status'] >= 400 && $resp['status'] < 600 ? $resp['status'] : 502, [
                'ok' => false,
                'error' => $resp['error'] ?? 'Export failed',
            ]);
        }

        $batch = cde_salesnav_collect_items($resp['data']);
        if ($batch === []) {
            break;
        }

        foreach ($batch as $row) {
            if (is_array($row)) {
                $collected[] = $row;
            }
        }

        $offset += count($batch);
        if (count($batch) < $limit) {
            break;
        }

        usleep(1500000);
    }

    return array_slice($collected, 0, $maxLeads);
}

function cde_salesnav_export(array $config, string $sourceUrl, string $mode, int $maxLeads): array
{
    if ($config['is_v1']) {
        return cde_salesnav_paginate_v1($config, $sourceUrl, $maxLeads);
    }

    if ($mode === 'search') {
        return cde_salesnav_paginate_v2_search($config, $sourceUrl, $maxLeads);
    }

    if (preg_match('#linkedin\.com/sales/lists/people/(?P<id>\d+)#i', $sourceUrl, $m)) {
        return cde_salesnav_paginate_v2_list($config, $m['id'], $maxLeads);
    }

    return cde_salesnav_paginate_v2_search($config, $sourceUrl, $maxLeads);
}

function cde_enforce_salesnav_rate_limits(int $limit): void
{
    $ip = cde_client_ip();
    cde_session_start();
    $sid = session_id() ?: $ip;

    if ($limit <= 25) {
        $checks = [
            cde_rate_consume('salesnav_demo_ip_hour', $ip, 8, 3600),
            cde_rate_consume('salesnav_demo_ip_day', $ip, 25, 86400),
            cde_rate_consume('salesnav_demo_sess', $sid, 5, 900),
        ];
    } else {
        $checks = [
            cde_rate_consume('salesnav_full_ip_hour', $ip, 3, 3600),
            cde_rate_consume('salesnav_full_ip_day', $ip, 10, 86400),
            cde_rate_consume('salesnav_full_sess', $sid, 2, 900),
        ];
    }

    foreach ($checks as $check) {
        if (!$check['ok']) {
            cde_json_response(429, [
                'ok' => false,
                'error' => 'Rate limit reached. Try again later or request volume access below.',
                'retry_after' => $check['retry_after'],
            ]);
        }
    }
}
