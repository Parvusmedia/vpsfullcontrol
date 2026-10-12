<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function hf_env_path(): string
{
    $fromEnv = getenv('HOME_FINANCE_ENV');
    if (is_string($fromEnv) && $fromEnv !== '') {
        return $fromEnv;
    }
    $candidates = [
        '/opt/apps/private/home-finance/app.env',
        '/var/www/vhosts/parvusmedia.com/private/home-finance/app.env',
        dirname(__DIR__, 2) . '/private/home-finance/app.env',
    ];
    foreach ($candidates as $path) {
        if (@is_readable($path)) {
            return $path;
        }
    }
    return '/var/www/vhosts/parvusmedia.com/private/home-finance/app.env';
}

function hf_load_env_file(string $path): void
{
    if (!is_readable($path)) {
        return;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return;
    }
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || (isset($line[0]) && $line[0] === '#')) {
            continue;
        }
        if (strpos($line, '=') === false) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value, " \t\"'");
        if ($key !== '' && getenv($key) === false) {
            putenv("$key=$value");
            $_ENV[$key] = $value;
        }
    }
}

hf_load_env_file(hf_env_path());

function hf_data_dir(): string
{
    $dir = getenv('HOME_FINANCE_DATA_DIR');
    if (is_string($dir) && $dir !== '') {
        return rtrim($dir, '/');
    }
    return '/var/www/vhosts/parvusmedia.com/private/home-finance/data';
}

function hf_api_token(): string
{
    $t = getenv('HOME_FINANCE_API_TOKEN');
    return is_string($t) ? $t : '';
}

function hf_require_auth(): void
{
    $expected = hf_api_token();
    if ($expected === '') {
        http_response_code(503);
        echo json_encode(['error' => 'server_not_configured']);
        exit;
    }
    $given = $_SERVER['HTTP_X_HOME_TOKEN'] ?? '';
    if (!is_string($given) || !hash_equals($expected, $given)) {
        http_response_code(401);
        echo json_encode(['error' => 'unauthorized']);
        exit;
    }
}

function hf_read_store(): array
{
    $path = hf_data_dir() . '/store.json';
    if (!is_readable($path)) {
        return hf_default_store();
    }
    $raw = file_get_contents($path);
    if ($raw === false || $raw === '') {
        return hf_default_store();
    }
    $data = json_decode($raw, true);
    if (!is_array($data)) {
        return hf_default_store();
    }
    return array_merge(hf_default_store(), $data);
}

function hf_default_store(): array
{
    return [
        'transactions' => [],
        'rules' => [
            ['pattern' => 'mercadona|carrefour|consum|lidl|aldi|eroski|dia|alcampo', 'category' => 'Alimentación', 'tags' => []],
            ['pattern' => 'netflix|spotify|hbo|disney|amazon prime|movistar|vodafone|orange|yoigo', 'category' => 'Suscripciones', 'tags' => []],
            ['pattern' => 'repsol|cepsa|petroprix|uber|cabify|renfe|emt|metro|bicing|taxi', 'category' => 'Transporte', 'tags' => []],
            ['pattern' => 'endesa|iberdrola|naturgy|agua|canal de isabel', 'category' => 'Hogar y suministros', 'tags' => []],
            ['pattern' => 'farmacia|sanitas|adeslas|quirón|mapfre', 'category' => 'Salud', 'tags' => []],
            ['pattern' => 'amazon|el corte inglés|zalando|zara', 'category' => 'Ropa', 'tags' => []],
            ['pattern' => 'traspaso|transferencia entre cuentas', 'category' => 'Finanzas', 'tags' => []],
        ],
        'fixed_categories' => ['Hogar y suministros', 'Suscripciones', 'Finanzas'],
        'categories' => [
            'Alimentación',
            'Hogar y suministros',
            'Transporte',
            'Salud',
            'Ocio',
            'Suscripciones',
            'Educación',
            'Ropa',
            'Finanzas',
            'Otros',
        ],
        'budgets' => [],
        'fixed_categories' => ['Hogar y suministros', 'Suscripciones', 'Finanzas'],
    ];
}

function hf_write_store(array $store): void
{
    $dir = hf_data_dir();
    if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) {
        throw new RuntimeException('cannot_create_data_dir');
    }
    $path = $dir . '/store.json';
    $json = json_encode($store, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    if ($json === false) {
        throw new RuntimeException('encode_failed');
    }
    $tmp = $path . '.tmp.' . getmypid();
    if (file_put_contents($tmp, $json, LOCK_EX) === false) {
        throw new RuntimeException('write_failed');
    }
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('rename_failed');
    }
    @chmod($path, 0600);
}

function hf_tx_id(array $row): string
{
    $parts = [
        (string) ($row['date'] ?? ''),
        (string) ($row['concept'] ?? ''),
        (string) ($row['amount'] ?? ''),
        (string) ($row['account'] ?? ''),
    ];
    return hash('sha256', implode('|', $parts));
}

function hf_normalize_concept(string $s): string
{
    $s = trim($s);
    $s = function_exists('mb_strtolower') ? mb_strtolower($s, 'UTF-8') : strtolower($s);
    return preg_replace('/\s+/', ' ', $s) ?? $s;
}

function hf_apply_rules(array $tx, array $rules): array
{
    if (($tx['category'] ?? '') !== '' && ($tx['category'] ?? '') !== 'Otros') {
        return $tx;
    }
    $concept = hf_normalize_concept((string) ($tx['concept'] ?? ''));
    foreach ($rules as $rule) {
        if (!is_array($rule)) {
            continue;
        }
        $pattern = (string) ($rule['pattern'] ?? '');
        $category = (string) ($rule['category'] ?? '');
        if ($pattern === '' || $category === '') {
            continue;
        }
        $re = '/' . str_replace('/', '\\/', $pattern) . '/iu';
        if (@preg_match($re, $concept) === 1) {
            $tx['category'] = $category;
            if (preg_match('/traspaso|transferencia/i', $concept)) {
                $tx['type'] = 'transferencia';
            }
            if (!empty($rule['tags']) && is_array($rule['tags'])) {
                $existing = $tx['tags'] ?? [];
                if (!is_array($existing)) {
                    $existing = [];
                }
                $tx['tags'] = array_values(array_unique(array_merge($existing, $rule['tags'])));
            }
            break;
        }
    }
    if (($tx['category'] ?? '') === '') {
        $tx['category'] = 'Otros';
    }
    return $tx;
}

function hf_json_body(): array
{
    $raw = file_get_contents('php://input');
    if ($raw === false || $raw === '') {
        return [];
    }
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

function hf_month_key(string $date): string
{
    if (preg_match('/^(\d{4})-(\d{2})/', $date, $m)) {
        return $m[1] . '-' . $m[2];
    }
    return '';
}
