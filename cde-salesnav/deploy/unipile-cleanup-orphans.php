#!/usr/bin/env php
<?php
declare(strict_types=1);

/**
 * List Unipile accounts vs SalesNav panel links (read-only by default).
 *
 * Deleting is disabled unless BOTH flags match exactly (human double-check):
 *   --delete=ACCOUNT_ID --confirm=ACCOUNT_ID
 *
 * Never run delete without explicit owner approval. Verify provider type first.
 *
 * Usage:
 *   php unipile-cleanup-orphans.php
 *   php unipile-cleanup-orphans.php --delete=ID --confirm=ID
 */

$docroot = getenv('CDE_DOCROOT') ?: '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_unipile.php';

$deleteId = null;
$confirmId = null;
foreach ($argv as $arg) {
    if (str_starts_with($arg, '--delete=')) {
        $deleteId = trim(substr($arg, strlen('--delete=')));
    } elseif (str_starts_with($arg, '--confirm=')) {
        $confirmId = trim(substr($arg, strlen('--confirm=')));
    } elseif ($arg === '--help' || $arg === '-h') {
        fwrite(STDOUT, "Usage: unipile-cleanup-orphans.php\n");
        fwrite(STDOUT, "       unipile-cleanup-orphans.php --delete=ACCOUNT_ID --confirm=ACCOUNT_ID\n");
        fwrite(STDOUT, "\nList mode is the default. Delete requires matching --delete and --confirm.\n");
        exit(0);
    }
}

/** @return array<string, true> */
function unipile_cleanup_protected_ids(): array
{
    $protected = [];
    foreach (cde_salesnav_load_accounts() as $userId => $rec) {
        if (!is_array($rec)) {
            continue;
        }
        $id = trim((string) ($rec['account_id'] ?? ''));
        if ($id !== '') {
            $protected[$id] = true;
        }
        $seat = cde_salesnav_find_reconnectable_seat((string) $userId);
        if ($seat !== null) {
            $protected[$seat] = true;
        }
    }

    return $protected;
}

function unipile_cleanup_account_type(array $item): string
{
    return strtoupper(trim((string) ($item['type'] ?? $item['provider'] ?? $item['provider_id'] ?? 'UNKNOWN')));
}

$protected = unipile_cleanup_protected_ids();
$items = cde_salesnav_list_unipile_account_items();

if ($deleteId !== null || $confirmId !== null) {
    if ($deleteId === null || $confirmId === null || $deleteId !== $confirmId) {
        fwrite(STDERR, "Delete refused: pass matching --delete=ID and --confirm=ID after explicit approval.\n");
        exit(2);
    }
    if (isset($protected[$deleteId])) {
        fwrite(STDERR, "Refusing to delete {$deleteId}: linked or reserved by the panel.\n");
        exit(2);
    }
    $target = null;
    foreach ($items as $item) {
        if (!is_array($item)) {
            continue;
        }
        $id = trim((string) ($item['id'] ?? $item['account_id'] ?? ''));
        if ($id === $deleteId) {
            $target = $item;
            break;
        }
    }
    if ($target === null) {
        fwrite(STDERR, "Account {$deleteId} not found in Unipile.\n");
        exit(1);
    }
    $provider = unipile_cleanup_account_type($target);
    if ($provider !== '' && $provider !== 'LINKEDIN') {
        fwrite(STDERR, "Refusing to delete {$deleteId}: provider is {$provider}, not LINKEDIN.\n");
        exit(2);
    }
    $cfg = cde_unipile_api_config(null);
    $resp = cde_unipile_request($cfg, 'DELETE', '/accounts/' . rawurlencode($deleteId));
    if (!$resp['ok']) {
        fwrite(STDERR, 'Delete failed: ' . ($resp['error'] ?? 'unknown') . "\n");
        exit(1);
    }
    fwrite(STDOUT, "Deleted {$deleteId} ({$provider})\n");
    exit(0);
}

fwrite(STDOUT, "Protected (panel): " . implode(', ', array_keys($protected)) . "\n\n");
fwrite(STDOUT, "Unipile accounts (list-only — delete needs --delete=ID --confirm=ID):\n");

foreach ($items as $item) {
    if (!is_array($item)) {
        continue;
    }
    $id = trim((string) ($item['id'] ?? $item['account_id'] ?? ''));
    if ($id === '') {
        continue;
    }
    $name = trim((string) ($item['name'] ?? ''));
    $provider = unipile_cleanup_account_type($item);
    $alive = cde_salesnav_is_account_alive($id);
    $role = isset($protected[$id]) ? 'KEEP (panel)' : 'orphan';
    $meta = $alive ? cde_salesnav_fetch_account_meta(cde_unipile_api_config($id), $id) : ['label' => ''];
    $label = trim((string) ($meta['label'] ?? ''));
    fwrite(STDOUT, sprintf(
        "- %s | %s | %s | %s | name=%s | %s\n",
        $id,
        $provider,
        $role,
        $alive ? 'alive' : 'dead/expired',
        $name !== '' ? $name : '—',
        $label !== '' ? $label : '—'
    ));
}
