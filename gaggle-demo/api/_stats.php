<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';

function ngaged_compute_stats(int $days): array
{
    ngaged_maybe_migrate_legacy();
    $store = ngaged_campaigns_store();
    $membersStore = ngaged_members_store();
    $memberNames = [];
    foreach ($membersStore['members'] ?? [] as $m) {
        if (!is_array($m)) {
            continue;
        }
        $memberNames[(string) ($m['id'] ?? '')] = (string) ($m['name'] ?? $m['email'] ?? 'Miembro');
    }

    $now = time();
    $fromTs = $days > 0 ? $now - ($days * 86400) : 0;

    $totals = [
        'campaigns' => 0,
        'invitesSent' => 0,
        'reposted' => 0,
        'declined' => 0,
        'pending' => 0,
        'adoptionRate' => 0.0,
        'medianHoursToRepost' => null,
        'campaignsThisMonth' => 0,
    ];

    $responseMix = ['reposted' => 0, 'declined' => 0, 'pending' => 0];
    $daily = [];
    $memberReposts = [];
    $hoursToRepost = [];
    $recentCampaigns = [];

    $monthStart = gmmktime(0, 0, 0, (int) gmdate('n'), 1, (int) gmdate('Y'));

    foreach ($store['campaigns'] ?? [] as $c) {
        if (!is_array($c) || empty($c['dispatchedAt'])) {
            continue;
        }
        $dispatchedAt = strtotime((string) $c['dispatchedAt']);
        if ($fromTs > 0 && $dispatchedAt !== false && $dispatchedAt < $fromTs) {
            continue;
        }

        $totals['campaigns']++;
        if ($dispatchedAt !== false && $dispatchedAt >= $monthStart) {
            $totals['campaignsThisMonth']++;
        }

        $dayKey = $dispatchedAt ? gmdate('Y-m-d', $dispatchedAt) : gmdate('Y-m-d');
        if (!isset($daily[$dayKey])) {
            $daily[$dayKey] = ['date' => $dayKey, 'campaigns' => 0, 'reposts' => 0];
        }
        $daily[$dayKey]['campaigns']++;

        $deliveries = $c['deliveries'] ?? [];
        $campReposted = 0;
        $campSent = 0;

        foreach ($deliveries as $d) {
            if (!is_array($d) || empty($d['sentAt'])) {
                continue;
            }
            $campSent++;
            $totals['invitesSent']++;
            $action = (string) ($d['action'] ?? '');
            if ($action === 'approve') {
                $totals['reposted']++;
                $responseMix['reposted']++;
                $campReposted++;
                $mid = (string) ($d['memberId'] ?? '');
                if ($mid !== '') {
                    $memberReposts[$mid] = ($memberReposts[$mid] ?? 0) + 1;
                }
                $sentTs = strtotime((string) $d['sentAt']);
                $respTs = strtotime((string) ($d['respondedAt'] ?? ''));
                if ($sentTs && $respTs && $respTs >= $sentTs) {
                    $hoursToRepost[] = ($respTs - $sentTs) / 3600;
                }
                $rDay = $respTs ? gmdate('Y-m-d', $respTs) : $dayKey;
                if (!isset($daily[$rDay])) {
                    $daily[$rDay] = ['date' => $rDay, 'campaigns' => 0, 'reposts' => 0];
                }
                $daily[$rDay]['reposts']++;
            } elseif ($action === 'decline') {
                $totals['declined']++;
                $responseMix['declined']++;
            } else {
                $totals['pending']++;
                $responseMix['pending']++;
            }
        }

        $closed = $totals['reposted'] + $totals['declined'];
        $rate = $campSent > 0 ? round(100 * $campReposted / $campSent, 1) : 0.0;
        $recentCampaigns[] = [
            'id' => (string) ($c['id'] ?? ''),
            'title' => (string) ($c['title'] ?? ''),
            'sent' => $campSent,
            'reposted' => $campReposted,
            'rate' => $rate,
            'createdAt' => (string) ($c['dispatchedAt'] ?? $c['createdAt'] ?? ''),
            'deliveries' => $deliveries,
        ];
    }

    $answered = $totals['reposted'] + $totals['declined'];
    if ($answered > 0) {
        $totals['adoptionRate'] = round(100 * $totals['reposted'] / $answered, 1);
    }

    if ($hoursToRepost !== []) {
        sort($hoursToRepost);
        $mid = (int) floor(count($hoursToRepost) / 2);
        $totals['medianHoursToRepost'] = round($hoursToRepost[$mid], 1);
    }

    ksort($daily);
    $dailyList = array_values($daily);
    if ($days > 0) {
        $cut = gmdate('Y-m-d', $now - ($days * 86400));
        $dailyList = array_values(array_filter($dailyList, static fn ($row) => ($row['date'] ?? '') >= $cut));
    }

    usort($recentCampaigns, static fn ($a, $b) => strcmp((string) ($b['createdAt'] ?? ''), (string) ($a['createdAt'] ?? '')));
    $recentCampaigns = array_slice($recentCampaigns, 0, 15);
    foreach ($recentCampaigns as &$rc) {
        unset($rc['deliveries']);
    }

    $topMembers = [];
    foreach ($memberReposts as $mid => $count) {
        $topMembers[] = [
            'memberId' => $mid,
            'name' => $memberNames[$mid] ?? ('Miembro ' . substr($mid, -6)),
            'reposts' => $count,
            'adoptionRate' => 100.0,
        ];
    }
    usort($topMembers, static fn ($a, $b) => ($b['reposts'] ?? 0) <=> ($a['reposts'] ?? 0));
    $topMembers = array_slice($topMembers, 0, 10);

    return [
        'period' => [
            'days' => $days,
            'from' => $fromTs > 0 ? gmdate('c', $fromTs) : null,
            'to' => gmdate('c'),
        ],
        'totals' => $totals,
        'series' => [
            'daily' => $dailyList,
            'responseMix' => $responseMix,
        ],
        'topMembers' => $topMembers,
        'recentCampaigns' => $recentCampaigns,
    ];
}
