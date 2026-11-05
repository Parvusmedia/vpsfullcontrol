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
