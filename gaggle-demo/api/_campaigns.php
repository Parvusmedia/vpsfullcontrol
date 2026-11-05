<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/_teams.php';
require_once __DIR__ . '/_members_util.php';

function ngaged_campaigns_store(): array
{
    return gaggle_demo_read_json_file('campaigns.json', ['campaigns' => []]);
}

function ngaged_save_campaigns(array $store): void
{
    gaggle_demo_write_json_file('campaigns.json', $store);
}

function ngaged_find_campaign(array $store, string $id): ?array
{
    foreach ($store['campaigns'] ?? [] as $i => $c) {
        if (is_array($c) && ($c['id'] ?? '') === $id) {
            return ['index' => $i, 'campaign' => $c];
        }
    }
    return null;
}

function ngaged_members_store(): array
{
    $store = ngaged_normalize_members_store(
        gaggle_demo_read_json_file('members.json', ['members' => [], 'teams' => []])
    );
    if ($store['teams'] === []) {
        $store = ngaged_seed_default_teams_if_empty($store);
        ngaged_save_members($store);
    }
    return $store;
}

function ngaged_save_members(array $store): void
{
    gaggle_demo_write_json_file('members.json', $store);
}

function ngaged_find_member(array $store, string $id): ?array
{
    foreach ($store['members'] ?? [] as $i => $m) {
        if (is_array($m) && ($m['id'] ?? '') === $id) {
            return ['index' => $i, 'member' => $m];
        }
    }
    return null;
}

/** Migrate legacy activities/responses into campaigns once. */
function ngaged_maybe_migrate_legacy(): void
{
    $store = ngaged_campaigns_store();
    if (!empty($store['campaigns'])) {
        return;
    }

    $activities = gaggle_demo_read_json_file('activities.json', ['activities' => []])['activities'] ?? [];
    if (!is_array($activities) || $activities === []) {
        return;
    }

    $responses = gaggle_demo_read_json_file('responses.json', ['responses' => []])['responses'] ?? [];
    $byActivity = [];
    foreach ($responses as $r) {
        if (!is_array($r)) {
            continue;
        }
        $aid = (string) ($r['activityId'] ?? '');
        $byActivity[$aid][] = $r;
    }

    $campaigns = [];
    foreach ($activities as $a) {
        if (!is_array($a)) {
            continue;
        }
        $id = gaggle_demo_new_id('camp');
        $deliveries = [];
        foreach ($byActivity[(string) ($a['id'] ?? '')] ?? [] as $r) {
            $deliveries[] = [
                'memberId' => '',
                'email' => '',
                'platformId' => (string) ($r['platformId'] ?? ''),
                'sentAt' => (string) ($a['createdAt'] ?? gmdate('c')),
                'respondedAt' => (string) ($r['completedAt'] ?? ''),
                'action' => (string) ($r['action'] ?? ''),
                'postGroupId' => $r['postGroupId'] ?? null,
                'error' => null,
            ];
        }
        $campaigns[] = [
            'id' => $id,
            'title' => (string) ($a['title'] ?? 'Campaña migrada'),
            'linkedinUrl' => '',
            'repostParentUrn' => (string) ($a['repostParentUrn'] ?? ''),
            'commentary' => (string) ($a['content'] ?? ''),
            'preview' => ['title' => '', 'description' => '', 'image' => ''],
            'memberIds' => [],
            'createdAt' => (string) ($a['createdAt'] ?? gmdate('c')),
            'dispatchedAt' => (string) ($a['createdAt'] ?? gmdate('c')),
            'status' => 'dispatched',
            'deliveries' => $deliveries,
        ];
    }

    if ($campaigns !== []) {
        ngaged_save_campaigns(['campaigns' => $campaigns]);
    }
}
