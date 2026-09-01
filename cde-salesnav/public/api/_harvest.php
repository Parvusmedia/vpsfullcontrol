<?php
/**
 * HarvestAPI enrichment for Sales Navigator exports (Enriched tier).
 * Docs: https://docs.harvestapi.io/linkedin-api-reference/profile/get
 */

declare(strict_types=1);

function cde_harvest_env_paths(): array
{
    return [
        dirname(__DIR__, 2) . '/private/cde/harvest.env',
        dirname(__DIR__, 2) . '/private/cde/apify.env',
    ];
}

function cde_harvest_read_env(): array
{
    $env = [];
    foreach (cde_harvest_env_paths() as $path) {
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
    }
    return $env;
}

function cde_harvest_config(): array
{
    $env = cde_harvest_read_env();
    $key = $env['HARVEST_API_KEY'] ?? $env['HARVESTAPI_KEY'] ?? getenv('HARVEST_API_KEY') ?: '';
    $base = rtrim($env['HARVEST_API_BASE'] ?? $env['HARVESTAPI_BASE_URL'] ?? 'https://api.harvestapi.io', '/');
    return [
        'api_key' => $key,
        'base_url' => $base,
        'timeout' => max(5, (int) ($env['HARVEST_API_TIMEOUT'] ?? 25)),
        'profile_main' => ($env['HARVEST_PROFILE_MAIN'] ?? '1') !== '0',
    ];
}

function cde_harvest_enabled(): bool
{
    return cde_harvest_config()['api_key'] !== '';
}

function cde_harvest_request(string $path, array $query = []): array
{
    $cfg = cde_harvest_config();
    if ($cfg['api_key'] === '') {
        return ['ok' => false, 'error' => 'Harvest API is not configured.'];
    }

    $url = $cfg['base_url'] . $path;
    if ($query !== []) {
        $url .= '?' . http_build_query($query);
    }

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            'Accept: application/json',
            'X-API-Key: ' . $cfg['api_key'],
        ],
        CURLOPT_TIMEOUT => $cfg['timeout'],
    ]);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'error' => $curlErr !== '' ? $curlErr : 'Harvest request failed'];
    }

    $data = json_decode((string) $raw, true);
    if (!is_array($data)) {
        return ['ok' => false, 'error' => 'Invalid Harvest response', 'status' => $code];
    }

    if ($code >= 400) {
        $msg = (string) ($data['message'] ?? $data['error'] ?? 'Harvest API error');
        return ['ok' => false, 'error' => $msg, 'status' => $code, 'data' => $data];
    }

    return ['ok' => true, 'status' => $code, 'data' => $data];
}

function cde_harvest_get_profile(string $linkedinUrl): array
{
    $query = ['url' => $linkedinUrl];
    if (cde_harvest_config()['profile_main']) {
        $query['main'] = 'true';
    }
    $resp = cde_harvest_request('/linkedin/profile', $query);
    if (!$resp['ok']) {
        return $resp;
    }
    $element = $resp['data']['element'] ?? null;
    if (!is_array($element)) {
        return ['ok' => false, 'error' => 'Profile not found in Harvest response'];
    }
    return ['ok' => true, 'profile' => $element];
}

function cde_harvest_get_company(string $companyUrl): array
{
    $resp = cde_harvest_request('/linkedin/company', ['url' => $companyUrl]);
    if (!$resp['ok']) {
        return $resp;
    }
    $element = $resp['data']['element'] ?? null;
    if (!is_array($element)) {
        return ['ok' => false, 'error' => 'Company not found in Harvest response'];
    }
    return ['ok' => true, 'company' => $element];
}

function cde_harvest_domain_from_website(?string $website): string
{
    $website = trim((string) $website);
    if ($website === '') {
        return '';
    }
    if (!preg_match('#^https?://#i', $website)) {
        $website = 'https://' . $website;
    }
    $host = parse_url($website, PHP_URL_HOST);
    if (!is_string($host) || $host === '') {
        return '';
    }
    return preg_replace('/^www\./i', '', $host) ?? $host;
}

function cde_harvest_parse_tenure_years(?string $duration): string
{
    $duration = trim((string) $duration);
    if ($duration === '') {
        return '';
    }
    if (preg_match('/(\d+)\s*yrs?/i', $duration, $m)) {
        return $m[1];
    }
    if (preg_match('/(\d+)\s*years?/i', $duration, $m)) {
        return $m[1];
    }
    return '';
}

function cde_harvest_infer_seniority(?string $position): string
{
    $position = strtolower(trim((string) $position));
    if ($position === '') {
        return '';
    }
    $map = [
        'chief' => 'C-Level',
        'ceo' => 'C-Level',
        'cto' => 'C-Level',
        'cfo' => 'C-Level',
        'coo' => 'C-Level',
        'founder' => 'Founder',
        'co-founder' => 'Founder',
        'president' => 'President',
        'vp ' => 'VP',
        'vice president' => 'VP',
        'director' => 'Director',
        'head of' => 'Director',
        'manager' => 'Manager',
        'senior' => 'Senior',
        'lead' => 'Lead',
        'intern' => 'Intern',
    ];
    foreach ($map as $needle => $label) {
        if (strpos($position, $needle) !== false) {
            return $label;
        }
    }
    return '';
}

function cde_harvest_join_skills(array $profile): string
{
    $names = [];
    foreach ($profile['skills'] ?? [] as $skill) {
        if (is_array($skill) && !empty($skill['name'])) {
            $names[] = (string) $skill['name'];
        } elseif (is_string($skill) && $skill !== '') {
            $names[] = $skill;
        }
    }
    if ($names === [] && !empty($profile['topSkills']) && is_array($profile['topSkills'])) {
        foreach ($profile['topSkills'] as $skill) {
            if (is_string($skill) && $skill !== '') {
                $names[] = $skill;
            }
        }
    }
    return implode('; ', array_slice(array_unique($names), 0, 25));
}

function cde_harvest_join_languages(array $profile): string
{
    $parts = [];
    foreach ($profile['languages'] ?? [] as $lang) {
        if (!is_array($lang)) {
            continue;
        }
        $name = trim((string) ($lang['name'] ?? ''));
        if ($name === '') {
            continue;
        }
        $prof = trim((string) ($lang['proficiency'] ?? ''));
        $parts[] = $prof !== '' ? $name . ' (' . $prof . ')' : $name;
    }
    return implode('; ', $parts);
}

function cde_harvest_company_size(array $company): string
{
    $range = $company['employeeCountRange'] ?? null;
    if (is_array($range)) {
        $start = $range['start'] ?? null;
        $end = $range['end'] ?? null;
        if ($start !== null && $end !== null) {
            return $start . '-' . $end;
        }
        if ($start !== null) {
            return (string) $start . '+';
        }
    }
    if (!empty($company['employeeCount'])) {
        return (string) $company['employeeCount'];
    }
    return '';
}

function cde_harvest_company_hq(array $company): string
{
    foreach ($company['locations'] ?? [] as $loc) {
        if (!is_array($loc)) {
            continue;
        }
        if (!empty($loc['headquarter'])) {
            $parsed = $loc['parsed']['text'] ?? null;
            if (is_string($parsed) && $parsed !== '') {
                return $parsed;
            }
            $bits = array_filter([
                $loc['city'] ?? '',
                $loc['geographicArea'] ?? '',
                $loc['country'] ?? '',
            ]);
            if ($bits !== []) {
                return implode(', ', $bits);
            }
        }
    }
    $first = $company['locations'][0] ?? null;
    if (is_array($first)) {
        return (string) ($first['parsed']['text'] ?? $first['city'] ?? '');
    }
    return '';
}

function cde_harvest_company_industry(array $company): string
{
    $names = [];
    foreach ($company['industries'] ?? [] as $ind) {
        if (is_array($ind) && !empty($ind['name'])) {
            $names[] = (string) $ind['name'];
        } elseif (is_array($ind) && !empty($ind['title'])) {
            $names[] = (string) $ind['title'];
        }
    }
    return implode('; ', array_unique($names));
}

/** @param array<string, mixed> $profile @param array<string, mixed>|null $company */
function cde_harvest_map_enriched_fields(array $profile, ?array $company, array $experience): array
{
    $position = (string) ($experience['position'] ?? $profile['headline'] ?? '');
    $companyUrl = (string) ($experience['companyLinkedinUrl'] ?? '');
    $website = is_array($company) ? (string) ($company['website'] ?? '') : '';

    return [
        'company_linkedin_url' => $companyUrl,
        'company_domain' => cde_harvest_domain_from_website($website),
        'company_industry' => is_array($company) ? cde_harvest_company_industry($company) : '',
        'company_size' => is_array($company) ? cde_harvest_company_size($company) : '',
        'company_hq' => is_array($company) ? cde_harvest_company_hq($company) : '',
        'seniority' => cde_harvest_infer_seniority($position),
        'tenure_years' => cde_harvest_parse_tenure_years((string) ($experience['duration'] ?? '')),
        'profile_summary' => trim((string) ($profile['about'] ?? '')),
        'skills' => cde_harvest_join_skills($profile),
        'languages' => cde_harvest_join_languages($profile),
    ];
}

/**
 * @param list<array<string, mixed>> $rows
 * @return list<array<string, mixed>>
 */
function cde_harvest_enrich_rows(array $rows): array
{
    if ($rows === [] || !cde_harvest_enabled()) {
        return $rows;
    }

    $count = count($rows);
    @set_time_limit(max(180, min(900, $count * 6)));

    $cfg = cde_harvest_config();
    $batchSize = max(3, min(15, (int) (getenv('HARVEST_BATCH_SIZE') ?: 10)));

    $profileJobs = [];
    foreach ($rows as $i => $row) {
        $url = trim((string) ($row['linkedin_url'] ?? ''));
        if ($url !== '') {
            $profileJobs[$i] = $url;
        }
    }

    $profilesByIndex = cde_harvest_fetch_profiles_batch($profileJobs, $batchSize, $cfg);
    $companyUrls = [];
    foreach ($profilesByIndex as $profile) {
        if (!is_array($profile)) {
            continue;
        }
        $experience = $profile['experience'][0] ?? $profile['currentPosition'][0] ?? [];
        if (!is_array($experience)) {
            continue;
        }
        $companyUrl = trim((string) ($experience['companyLinkedinUrl'] ?? ''));
        if ($companyUrl !== '') {
            $companyUrls[$companyUrl] = true;
        }
    }

    $companyCache = cde_harvest_fetch_companies_batch(array_keys($companyUrls), $batchSize, $cfg);

    foreach ($rows as $i => $row) {
        $profile = $profilesByIndex[$i] ?? null;
        if (!is_array($profile)) {
            continue;
        }
        $experience = $profile['experience'][0] ?? $profile['currentPosition'][0] ?? [];
        if (!is_array($experience)) {
            $experience = [];
        }
        $companyUrl = trim((string) ($experience['companyLinkedinUrl'] ?? ''));
        $company = ($companyUrl !== '' && isset($companyCache[$companyUrl])) ? $companyCache[$companyUrl] : null;
        $rows[$i] = array_merge($row, cde_harvest_map_enriched_fields($profile, $company, $experience));
    }

    return $rows;
}

/**
 * @param array<int, string> $jobs index => linkedin profile url
 * @return array<int, array<string, mixed>|null>
 */
function cde_harvest_fetch_profiles_batch(array $jobs, int $batchSize, array $cfg): array
{
    $out = [];
    $chunks = array_chunk($jobs, $batchSize, true);
    foreach ($chunks as $chunk) {
        $requests = [];
        foreach ($chunk as $idx => $url) {
            $query = ['url' => $url];
            if (!empty($cfg['profile_main'])) {
                $query['main'] = 'true';
            }
            $requests[$idx] = ['/linkedin/profile', $query];
        }
        $responses = cde_harvest_multi_request($requests, $cfg);
        foreach ($chunk as $idx => $url) {
            $resp = $responses[$idx] ?? ['ok' => false];
            $out[$idx] = ($resp['ok'] && is_array($resp['profile'] ?? null)) ? $resp['profile'] : null;
        }
    }
    return $out;
}

/**
 * @param list<string> $urls
 * @return array<string, array<string, mixed>>
 */
function cde_harvest_fetch_companies_batch(array $urls, int $batchSize, array $cfg): array
{
    $cache = [];
    if ($urls === []) {
        return $cache;
    }
    $chunks = array_chunk($urls, $batchSize);
    foreach ($chunks as $chunk) {
        $requests = [];
        foreach ($chunk as $i => $url) {
            $requests['c' . $i] = ['/linkedin/company', ['url' => $url]];
        }
        $responses = cde_harvest_multi_request($requests, $cfg);
        foreach ($chunk as $i => $url) {
            $resp = $responses['c' . $i] ?? ['ok' => false];
            if ($resp['ok'] && is_array($resp['company'] ?? null)) {
                $cache[$url] = $resp['company'];
            }
        }
    }
    return $cache;
}

/**
 * @param array<int|string, array{0: string, 1: array<string, string>}> $requests
 * @return array<int|string, array<string, mixed>>
 */
function cde_harvest_multi_request(array $requests, array $cfg): array
{
    $results = [];
    if ($requests === []) {
        return $results;
    }

    $mh = curl_multi_init();
    $handles = [];
    foreach ($requests as $key => $req) {
        [$path, $query] = $req;
        $url = $cfg['base_url'] . $path . '?' . http_build_query($query);
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => [
                'Accept: application/json',
                'X-API-Key: ' . $cfg['api_key'],
            ],
            CURLOPT_TIMEOUT => $cfg['timeout'],
        ]);
        curl_multi_add_handle($mh, $ch);
        $handles[$key] = $ch;
    }

    $running = null;
    do {
        $status = curl_multi_exec($mh, $running);
        if ($running > 0) {
            curl_multi_select($mh, 1.0);
        }
    } while ($running > 0 && $status === CURLM_OK);

    foreach ($handles as $key => $ch) {
        $raw = curl_multi_getcontent($ch);
        $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_multi_remove_handle($mh, $ch);
        curl_close($ch);

        $parsed = ['ok' => false];
        if ($raw !== false && $raw !== '') {
            $data = json_decode($raw, true);
            if (is_array($data) && $code < 400 && is_array($data['element'] ?? null)) {
                $element = $data['element'];
                if (strpos((string) $requests[$key][0], '/company') !== false) {
                    $parsed = ['ok' => true, 'company' => $element];
                } else {
                    $parsed = ['ok' => true, 'profile' => $element];
                }
            }
        }
        $results[$key] = $parsed;
    }

    curl_multi_close($mh);
    return $results;
}
