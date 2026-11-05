<?php

declare(strict_types=1);

/** @return array{teams:array<int,array>,members:array<int,array>} */
function ngaged_normalize_members_store(array $store): array
{
    if (!isset($store['members']) || !is_array($store['members'])) {
        $store['members'] = [];
    }
    if (!isset($store['teams']) || !is_array($store['teams'])) {
        $store['teams'] = [];
    }
    return $store;
}

function ngaged_seed_default_teams_if_empty(array $store): array
{
    if (($store['teams'] ?? []) !== []) {
        return $store;
    }
    $store['teams'] = [
        ['id' => 'team_marketing', 'name' => 'Marketing'],
        ['id' => 'team_ventas', 'name' => 'Ventas'],
        ['id' => 'team_general', 'name' => 'General'],
    ];
    return $store;
}

function ngaged_find_team(array $store, string $teamId): ?array
{
    foreach ($store['teams'] ?? [] as $i => $t) {
        if (is_array($t) && ($t['id'] ?? '') === $teamId) {
            return ['index' => $i, 'team' => $t];
        }
    }
    return null;
}

function ngaged_team_name_map(array $store): array
{
    $map = [];
    foreach ($store['teams'] ?? [] as $t) {
        if (is_array($t) && ($t['id'] ?? '') !== '') {
            $map[(string) $t['id']] = (string) ($t['name'] ?? '');
        }
    }
    return $map;
}

function ngaged_members_in_team(array $members, string $teamId): array
{
    $out = [];
    foreach ($members as $m) {
        if (!is_array($m)) {
            continue;
        }
        if ((string) ($m['teamId'] ?? '') === $teamId) {
            $out[] = $m;
        }
    }
    return $out;
}
