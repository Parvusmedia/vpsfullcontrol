#!/usr/bin/env php
<?php
declare(strict_types=1);

/**
 * List or delete Unipile accounts not referenced by the SalesNav panel.
 *
 * Usage:
 *   php unipile-cleanup-orphans.php              # list only (safe)
 *   php unipile-cleanup-orphans.php --delete ID  # delete one orphan (irreversible)
 */

$docroot = getenv('CDE_DOCROOT') ?: '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_bootstrap.php';
require $docroot . '/api/_unipile.php';

$deleteId = null;
foreach ($argv as $arg) {
    if (str_starts_with($arg, '--delete=')) {
        $deleteId = trim(substr($arg, strlen('--delete=')));
    } elseif ($arg === '--help' || $arg === '-h') {
        fwrite(STDOUT, "Usage: unipile-cleanup-orphans.php [--delete=ACCOUNT_ID]\n");
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

$protected = unipile_cleanup_protected_ids();
$items = cde_salesnav_list_unipile_account_items();

if ($deleteId !== null) {
    if (isset($protected[$deleteId])) {
        fwrite(STDERR, "Refusing to delete {$deleteId}: linked or reserved by the panel.\n");
        exit(2);
    }
    $exists = false;
    foreach ($items as $item) {
        if (!is_array($item)) {
            continue;
        }
        $id = trim((string) ($item['id'] ?? $item['account_id'] ?? ''));
        if ($id === $deleteId) {
            $exists = true;
            break;
        }
    }
    if (!$exists) {
        fwrite(STDERR, "Account {$deleteId} not found in Unipile.\n");
        exit(1);
    }
    $cfg = cde_unipile_api_config(null);
    $resp = cde_unipile_request($cfg, 'DELETE', '/accounts/' . rawurlencode($deleteId));
    if (!$resp['ok']) {
        fwrite(STDERR, 'Delete failed: ' . ($resp['error'] ?? 'unknown') . "\n");
        exit(1);
    }
    fwrite(STDOUT, "Deleted {$deleteId}\n");
    exit(0);
}

fwrite(STDOUT, "Protected (panel): " . implode(', ', array_keys($protected)) . "\n\n");
fwrite(STDOUT, "Unipile accounts:\n");

foreach ($items as $item) {
    if (!is_array($item)) {
        continue;
    }
    $id = trim((string) ($item['id'] ?? $item['account_id'] ?? ''));
    if ($id === '') {
        continue;
    }
    $name = trim((string) ($item['name'] ?? ''));
    $alive = cde_salesnav_is_account_alive($id);
    $role = isset($protected[$id]) ? 'KEEP (panel)' : 'orphan';
    $meta = $alive ? cde_salesnav_fetch_account_meta(cde_unipile_api_config($id), $id) : ['label' => ''];
    $label = trim((string) ($meta['label'] ?? ''));
    $hint = $role === 'orphan' ? '  → can delete with --delete=' . $id : '';
    fwrite(STDOUT, sprintf(
        "- %s | %s | %s | wallet=%s | %s%s\n",
        $id,
        $role,
        $alive ? 'alive' : 'dead/expired',
        $name !== '' ? $name : '—',
        $label !== '' ? $label : '—',
        $hint
    ));
}

fwrite(STDOUT, "\nDelete example: php unipile-cleanup-orphans.php --delete=ACCOUNT_ID\n");
