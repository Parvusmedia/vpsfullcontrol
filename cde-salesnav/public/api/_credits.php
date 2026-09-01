<?php
/**
 * Prepaid export credits (1 credit ≈ 1 Basic export).
 * Minimum top-up €20. +20% bonus from 100 base credits paid.
 */

declare(strict_types=1);

require_once __DIR__ . '/_unipile.php';

const CDE_CREDITS_MIN_EUR_CENTS = 2000;
const CDE_CREDITS_BONUS_THRESHOLD = 100;
const CDE_CREDITS_BONUS_PERCENT = 20;

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

/** Credits granted for a paid base amount (100 → 120 with +20%). */
function cde_credits_grant_for_base(int $paidBase): int
{
    if ($paidBase <= 0) {
        return 0;
    }
    if ($paidBase >= CDE_CREDITS_BONUS_THRESHOLD) {
        return (int) round($paidBase * (1 + CDE_CREDITS_BONUS_PERCENT / 100));
    }
    return $paidBase;
}

/**
 * @return array<string, array{
 *   paid_base: int,
 *   credits: int,
 *   amount_cents: int,
 *   label: string,
 *   bonus_credits: int
 * }>
 */
function cde_credits_packs(): array
{
    // Prepaid tiers: €20 starter, €29/€49/€99 volume packs (+20% bonus from 100 base credits).
    $defs = [
        '240' => ['paid_base' => 200, 'amount_cents' => 2000, 'label' => '240 credits (200 + 20% bonus) · ~€0.083/export'],
        '600' => ['paid_base' => 500, 'amount_cents' => 2900, 'label' => '600 credits (500 + 20% bonus) · ~€0.048/export'],
        '1800' => ['paid_base' => 1500, 'amount_cents' => 4900, 'label' => '1,800 credits (1,500 + 20% bonus) · ~€0.027/export'],
        '4800' => ['paid_base' => 4000, 'amount_cents' => 9900, 'label' => '4,800 credits (4,000 + 20% bonus) · ~€0.021/export'],
    ];
    $packs = [];
    foreach ($defs as $id => $def) {
        $granted = cde_credits_grant_for_base($def['paid_base']);
        $packs[$id] = [
            'paid_base' => $def['paid_base'],
            'credits' => $granted,
            'amount_cents' => $def['amount_cents'],
            'label' => $def['label'],
            'bonus_credits' => $granted - $def['paid_base'],
        ];
    }
    return $packs;
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

function cde_credits_ledger_has_ref(string $ref): bool
{
    $ref = trim($ref);
    if ($ref === '') {
        return false;
    }
    $path = cde_credits_ledger_file();
    if (!is_readable($path)) {
        return false;
    }
    $needle = '"ref":"' . str_replace(['\\', '"'], ['\\\\', '\\"'], $ref) . '"';
    $handle = fopen($path, 'rb');
    if ($handle === false) {
        return false;
    }
    while (!feof($handle)) {
        $line = fgets($handle);
        if ($line === false) {
            break;
        }
        if (strpos($line, $needle) !== false) {
            fclose($handle);
            return true;
        }
    }
    fclose($handle);
    return false;
}

function cde_credits_merge_wallets(string $fromUserId, string $toUserId): void
{
    $fromUserId = trim($fromUserId);
    $toUserId = trim($toUserId);
    if ($fromUserId === '' || $toUserId === '' || $fromUserId === $toUserId) {
        return;
    }
    $wallets = cde_credits_load_wallets();
    $fromBal = max(0, (int) ($wallets[$fromUserId]['balance'] ?? 0));
    if ($fromBal <= 0) {
        return;
    }
    $toBal = max(0, (int) ($wallets[$toUserId]['balance'] ?? 0));
    $wallets[$toUserId] = [
        'balance' => $toBal + $fromBal,
        'updated_at' => gmdate('c'),
    ];
    $wallets[$fromUserId] = [
        'balance' => 0,
        'updated_at' => gmdate('c'),
    ];
    cde_credits_save_wallets($wallets);
    cde_credits_append_ledger([
        'user_id' => $toUserId,
        'delta' => $fromBal,
        'balance' => $toBal + $fromBal,
        'ref' => 'merge:' . $fromUserId,
        'meta' => ['from_user_id' => $fromUserId],
    ]);
}

function cde_credits_add(string $userId, int $amount, string $ref, array $meta = []): int
{
    if ($amount <= 0) {
        return cde_credits_get_balance($userId);
    }
    if (cde_credits_ledger_has_ref($ref)) {
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

/** @return array{basic: bool, enriched: bool, mail: bool} */
function cde_credits_parse_tiers(array $payload): array
{
    return [
        'basic' => true,
        'enriched' => !empty($payload['tier_enriched']),
        'mail' => !empty($payload['tier_mail']),
    ];
}

/**
 * Cost in credits for an export (Basic=1, +Enriched=0.4/lead, +Mail=1/email found).
 *
 * @param list<array<string, mixed>> $rows
 */
function cde_credits_export_cost(array $rows, array $tiers): int
{
    $count = count($rows);
    if ($count === 0) {
        return 0;
    }

    $perRow = 1.0;
    if (!empty($tiers['enriched'])) {
        $perRow += 0.4;
    }
    $total = (int) ceil($count * $perRow);

    if (!empty($tiers['mail'])) {
        $emails = 0;
        foreach ($rows as $row) {
            $email = trim((string) ($row['work_email'] ?? ''));
            if ($email !== '') {
                $emails++;
            }
        }
        $total += (int) ceil($emails * 1.0);
    }

    return max(1, $total);
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
        'error' => 'Add export credits before connecting LinkedIn (minimum €20).',
        'balance' => 0,
        'min_eur' => CDE_CREDITS_MIN_EUR_CENTS / 100,
    ]);
}
