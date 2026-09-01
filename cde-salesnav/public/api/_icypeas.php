<?php
/**
 * Icypeas work-email discovery for Sales Navigator Mail tier.
 * Docs: https://api-doc.icypeas.com/getting-started/
 */

declare(strict_types=1);

function cde_icypeas_env_paths(): array
{
    return [
        dirname(__DIR__, 2) . '/private/cde/icypeas.env',
        '/opt/apps/private/cde/icypeas.env',
        '/opt/apps/companydataenrichment/private/cde/icypeas.env',
    ];
}

/** @return array<string, string> */
function cde_icypeas_read_env(): array
{
    static $cache = null;
    if (is_array($cache)) {
        return $cache;
    }
    $cache = [];
    foreach (cde_icypeas_env_paths() as $path) {
        if (!is_readable($path)) {
            continue;
        }
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $cache[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }
    return $cache;
}

/** @return array{api_key: string, base_url: string, timeout: int, poll_max: int, poll_sleep_ms: int} */
function cde_icypeas_config(): array
{
    $env = cde_icypeas_read_env();
    $base = rtrim($env['ICYPEAS_API_BASE'] ?? 'https://app.icypeas.com/api', '/');
    return [
        'api_key' => trim($env['ICYPEAS_API_KEY'] ?? getenv('ICYPEAS_API_KEY') ?: ''),
        'base_url' => $base,
        'timeout' => max(5, (int) ($env['ICYPEAS_TIMEOUT'] ?? 25)),
        'poll_max' => max(3, (int) ($env['ICYPEAS_POLL_MAX'] ?? 20)),
        'poll_sleep_ms' => max(200, (int) ($env['ICYPEAS_POLL_SLEEP_MS'] ?? 1500)),
    ];
}

function cde_icypeas_enabled(): bool
{
    return cde_icypeas_config()['api_key'] !== '';
}

/** @return array{ok: bool, error?: string, status?: int, data?: array<string, mixed>} */
function cde_icypeas_post(string $path, array $body): array
{
    $cfg = cde_icypeas_config();
    if ($cfg['api_key'] === '') {
        return ['ok' => false, 'error' => 'Icypeas API is not configured.'];
    }

    $url = $cfg['base_url'] . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'Accept: application/json',
            'Content-Type: application/json',
            'Authorization: ' . $cfg['api_key'],
        ],
        CURLOPT_POSTFIELDS => json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        CURLOPT_TIMEOUT => $cfg['timeout'],
    ]);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'error' => $curlErr !== '' ? $curlErr : 'Icypeas request failed'];
    }

    $data = json_decode((string) $raw, true);
    if (!is_array($data)) {
        return ['ok' => false, 'error' => 'Invalid Icypeas response', 'status' => $code];
    }
    if ($code >= 400 || empty($data['success'])) {
        $msg = (string) ($data['message'] ?? $data['error'] ?? 'Icypeas API error');
        return ['ok' => false, 'error' => $msg, 'status' => $code, 'data' => $data];
    }

    return ['ok' => true, 'status' => $code, 'data' => $data];
}

function cde_icypeas_is_pending_status(string $status): bool
{
    $status = strtoupper(trim($status));
    return in_array($status, ['NONE', 'SCHEDULED', 'IN_PROGRESS', 'PENDING', 'PROCESSING'], true);
}

/** @return array{work_email: string, email_status: string, email_confidence: string, email_source: string} */
function cde_icypeas_empty_result(string $status = 'not_found'): array
{
    return [
        'work_email' => '',
        'email_status' => $status,
        'email_confidence' => '',
        'email_source' => 'icypeas',
    ];
}

/** @param array<string, mixed> $item */
function cde_icypeas_parse_read_item(array $item): array
{
    $status = strtoupper(trim((string) ($item['status'] ?? '')));
    if (cde_icypeas_is_pending_status($status)) {
        return cde_icypeas_empty_result('pending');
    }

    $results = is_array($item['results'] ?? null) ? $item['results'] : [];
    $emails = is_array($results['emails'] ?? null) ? $results['emails'] : [];
    $best = null;
    foreach ($emails as $entry) {
        if (!is_array($entry)) {
            continue;
        }
        $email = trim((string) ($entry['email'] ?? ''));
        if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
            continue;
        }
        $best = $entry;
        break;
    }

    if ($best === null) {
        return cde_icypeas_empty_result('not_found');
    }

    return [
        'work_email' => trim((string) ($best['email'] ?? '')),
        'email_status' => 'found',
        'email_confidence' => trim((string) ($best['certainty'] ?? '')),
        'email_source' => trim((string) ($best['mxProvider'] ?? 'icypeas')),
    ];
}

/**
 * @return array{work_email: string, email_status: string, email_confidence: string, email_source: string}
 */
function cde_icypeas_find_email(string $firstName, string $lastName, string $domainOrCompany): array
{
    $firstName = trim($firstName);
    $lastName = trim($lastName);
    $domainOrCompany = trim($domainOrCompany);

    if ($domainOrCompany === '' || ($firstName === '' && $lastName === '')) {
        return cde_icypeas_empty_result('skipped');
    }

    $start = cde_icypeas_post('/email-search', [
        'firstname' => $firstName,
        'lastname' => $lastName,
        'domainOrCompany' => $domainOrCompany,
    ]);
    if (!$start['ok']) {
        return cde_icypeas_empty_result('error');
    }

    $searchId = trim((string) ($start['data']['item']['_id'] ?? $start['data']['item']['id'] ?? ''));
    if ($searchId === '') {
        return cde_icypeas_empty_result('error');
    }

    $cfg = cde_icypeas_config();
    for ($attempt = 0; $attempt < $cfg['poll_max']; $attempt++) {
        if ($attempt > 0) {
            usleep($cfg['poll_sleep_ms'] * 1000);
        }

        $read = cde_icypeas_post('/bulk-single-searchs/read', ['id' => $searchId]);
        if (!$read['ok']) {
            return cde_icypeas_empty_result('error');
        }

        $items = $read['data']['items'] ?? [];
        if (!is_array($items) || $items === []) {
            continue;
        }

        $parsed = cde_icypeas_parse_read_item(is_array($items[0]) ? $items[0] : []);
        if (($parsed['email_status'] ?? '') !== 'pending') {
            return $parsed;
        }
    }

    return cde_icypeas_empty_result('timeout');
}

function cde_icypeas_domain_or_company(array $row): string
{
    $domain = trim((string) ($row['company_domain'] ?? ''));
    if ($domain !== '') {
        return $domain;
    }

    $company = trim((string) ($row['company_name'] ?? ''));
    if ($company === '') {
        return '';
    }

    if (preg_match('#^https?://#i', $company)) {
        $host = parse_url($company, PHP_URL_HOST);
        if (is_string($host) && $host !== '') {
            return preg_replace('/^www\./i', '', $host) ?? $host;
        }
    }

    if (str_contains($company, '.') && !str_contains($company, ' ')) {
        return preg_replace('/^www\./i', '', $company) ?? $company;
    }

    return $company;
}

/**
 * @param list<array<string, mixed>> $rows
 * @return list<array<string, mixed>>
 */
function cde_icypeas_enrich_rows(array $rows): array
{
    if ($rows === [] || !cde_icypeas_enabled()) {
        return $rows;
    }

    $count = count($rows);
    @set_time_limit(max(300, min(3600, $count * 45)));

    foreach ($rows as $i => $row) {
        if (trim((string) ($row['work_email'] ?? '')) !== '') {
            continue;
        }

        $first = trim((string) ($row['first_name'] ?? ''));
        $last = trim((string) ($row['last_name'] ?? ''));
        if ($first === '' && $last === '') {
            $full = trim((string) ($row['full_name'] ?? ''));
            if ($full !== '') {
                $parts = preg_split('/\s+/', $full, 2) ?: [];
                $first = (string) ($parts[0] ?? '');
                $last = (string) ($parts[1] ?? '');
            }
        }

        $domainOrCompany = cde_icypeas_domain_or_company($row);
        $mail = cde_icypeas_find_email($first, $last, $domainOrCompany);
        $rows[$i] = array_merge($row, $mail);
    }

    return $rows;
}

/** @return list<string> */
function cde_icypeas_csv_columns(): array
{
    return ['work_email', 'email_status', 'email_confidence', 'email_source'];
}
