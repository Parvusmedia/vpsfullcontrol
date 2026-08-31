<?php
/**
 * Prepaid export credits (1 credit = 1 lead row in CSV, Basic tier).
 */

declare(strict_types=1);

require_once __DIR__ . '/_unipile.php';

function cde_credits_env_paths(): array
{
    return [
        dirname(__DIR__, 2) . '/private/cde/stripe.env',
        dirname(__DIR__, 2) . '/private/cde/unipile.env',
    ];
}

function cde_credits_read_env(): array
{
    $env = [];
    foreach (cde_credits_env_paths() as $path) {
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

function cde_credits_billing_enabled(): bool
{
    $env = cde_credits_read_env();
    if (($env['SALESNAV_BILLING_ENABLED'] ?? '') === '0') {
        return false;
    }
    $key = $env['STRIPE_SECRET_KEY'] ?? getenv('STRIPE_SECRET_KEY') ?: '';
    return $key !== '';
}

/** @return array<string, array{credits: int, amount_cents: int, label: string}> */
function cde_credits_packs(): array
{
    return [
        '100' => ['credits' => 100, 'amount_cents' => 500, 'label' => '100 export credits'],
        '500' => ['credits' => 500, 'amount_cents' => 2500, 'label' => '500 export credits'],
        '1000' => ['credits' => 1000, 'amount_cents' => 5000, 'label' => '1,000 export credits'],
    ];
}

function cde_credits_wallet_file(): string
{
    $dir = cde_salesnav_private_dir();
    return $dir . '/salesnav_wallets.json';
}

function cde_credits_ledger_file(): string
{
    $dir = cde_salesnav_private_dir();
    return $dir . '/salesnav_credits_ledger.jsonl';
}

function cde_credits_load_wallets(): array
{
    $path = cde_credits_wallet_file();
    if (!is_readable($path)) {
        return [];
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

function cde_credits_save_wallets(array $wallets): void
{
    $path = cde_credits_wallet_file();
    @file_put_contents($path, json_encode($wallets, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
    @chmod($path, 0600);
}

function cde_credits_get_balance(?string $userId = null): int
{
    $userId = $userId ?? cde_salesnav_user_id();
    $wallet = cde_credits_load_wallets()[$userId] ?? [];
    return max(0, (int) ($wallet['balance'] ?? 0));
}

function cde_credits_append_ledger(array $entry): void
{
    $entry['ts'] = gmdate('c');
    $line = json_encode($entry, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($line === false) {
        return;
    }
    @file_put_contents(cde_credits_ledger_file(), $line . "\n", FILE_APPEND | LOCK_EX);
}

function cde_credits_add(string $userId, int $amount, string $ref, array $meta = []): int
{
    if ($amount <= 0) {
        return cde_credits_get_balance($userId);
    }
    $wallets = cde_credits_load_wallets();
    $prev = max(0, (int) ($wallets[$userId]['balance'] ?? 0));
    $next = $prev + $amount;
    $wallets[$userId] = [
        'balance' => $next,
        'updated_at' => gmdate('c'),
    ];
    cde_credits_save_wallets($wallets);
    cde_credits_append_ledger([
        'user_id' => $userId,
        'delta' => $amount,
        'balance' => $next,
        'ref' => $ref,
        'meta' => $meta,
    ]);
    return $next;
}

function cde_credits_consume(string $userId, int $amount, string $ref, array $meta = []): bool
{
    if ($amount <= 0) {
        return true;
    }
    if (!cde_credits_billing_enabled()) {
        return true;
    }
    $wallets = cde_credits_load_wallets();
    $prev = max(0, (int) ($wallets[$userId]['balance'] ?? 0));
    if ($prev < $amount) {
        return false;
    }
    $next = $prev - $amount;
    $wallets[$userId] = [
        'balance' => $next,
        'updated_at' => gmdate('c'),
    ];
    cde_credits_save_wallets($wallets);
    cde_credits_append_ledger([
        'user_id' => $userId,
        'delta' => -$amount,
        'balance' => $next,
        'ref' => $ref,
        'meta' => $meta,
    ]);
    return true;
}

function cde_credits_require_positive_balance(): void
{
    if (!cde_credits_billing_enabled()) {
        return;
    }
    $balance = cde_credits_get_balance();
    if ($balance > 0) {
        return;
    }
    cde_json_response(402, [
        'ok' => false,
        'needs_payment' => true,
        'error' => 'Add export credits before connecting LinkedIn.',
        'balance' => 0,
    ]);
}
