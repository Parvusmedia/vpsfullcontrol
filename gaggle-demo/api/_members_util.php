<?php

declare(strict_types=1);

/** Elige el registro más completo cuando hay emails duplicados. */
function ngaged_pick_richer_member(array $a, array $b): array
{
    $score = static function (array $m): int {
        $s = 0;
        if (trim((string) ($m['platformId'] ?? '')) !== '') {
            $s += 8;
        }
        if (is_array($m['termsAcceptance'] ?? null)) {
            $s += 4;
        }
        if (trim((string) ($m['teamId'] ?? '')) !== '') {
            $s += 2;
        }
        if (trim((string) ($m['name'] ?? '')) !== '') {
            $s += 1;
        }
        $t = strtotime((string) ($m['linkedAt'] ?? $m['createdAt'] ?? ''));
        if ($t) {
            $s += min(3, (int) floor($t / 1_000_000_000));
        }
        return $s;
    };
    return $score($a) >= $score($b) ? $a : $b;
}

/** @return array{store:array,removed:int} */
function ngaged_deduplicate_members_store(array $store): array
{
    $members = $store['members'] ?? [];
    if (!is_array($members)) {
        $members = [];
    }
    $byEmail = [];
    $skipped = 0;
    foreach ($members as $m) {
        if (!is_array($m)) {
            $skipped++;
            continue;
        }
        $email = strtolower(trim((string) ($m['email'] ?? '')));
        if ($email === '') {
            $skipped++;
            continue;
        }
        if (!isset($byEmail[$email])) {
            $byEmail[$email] = $m;
            continue;
        }
        $byEmail[$email] = ngaged_pick_richer_member($byEmail[$email], $m);
    }
    $deduped = array_values($byEmail);
    $removed = max(0, count($members) - count($deduped) - $skipped);
    $store['members'] = $deduped;
    return ['store' => $store, 'removed' => $removed];
}

/** Estado normalizado del miembro en el panel. */
function ngaged_member_connect_status(array $m): string
{
    $st = strtolower(trim((string) ($m['connectStatus'] ?? '')));
    $platformId = trim((string) ($m['platformId'] ?? ''));
    $approvedAt = trim((string) ($m['approvedAt'] ?? ''));

    if ($st === 'active' || ($st === 'linked' && $approvedAt !== '')) {
        return 'active';
    }
    if ($st === 'linked' && $platformId !== '') {
        return 'active';
    }
    if ($st === 'pending_review' || ($platformId !== '' && $approvedAt === '')) {
        return 'pending_review';
    }
    if ($st === 'invited') {
        return 'invited';
    }
    if ($platformId !== '') {
        return $approvedAt !== '' ? 'active' : 'pending_review';
    }
    if ($st !== '') {
        return $st;
    }

    return 'pending';
}

function ngaged_member_ready_for_campaigns(array $m): bool
{
    return ngaged_member_connect_status($m) === 'active'
        && trim((string) ($m['platformId'] ?? '')) !== '';
}

/** Migración suave: registros antiguos «linked» con LinkedIn siguen activos. */
function ngaged_normalize_member_row(array $m): array
{
    $m = ngaged_migrate_legacy_member_status($m);
    $st = ngaged_member_connect_status($m);
    $m['connectStatus'] = $st;

    return $m;
}

function ngaged_migrate_legacy_member_status(array $m): array
{
    $platformId = trim((string) ($m['platformId'] ?? ''));
    $st = strtolower(trim((string) ($m['connectStatus'] ?? '')));
    if ($platformId === '') {
        return $m;
    }
    if ($st === 'linked' || ($st === '' && !empty($m['linkedAt']))) {
        if (trim((string) ($m['approvedAt'] ?? '')) === '') {
            $m['approvedAt'] = (string) ($m['linkedAt'] ?? gmdate('c'));
        }
        $m['connectStatus'] = 'active';
    }

    return $m;
}

function ngaged_find_member_by_email(array $store, string $email): ?array
{
    $email = strtolower(trim($email));
    foreach ($store['members'] ?? [] as $i => $m) {
        if (is_array($m) && strtolower((string) ($m['email'] ?? '')) === $email) {
            return ['index' => $i, 'member' => $m];
        }
    }
    return null;
}
