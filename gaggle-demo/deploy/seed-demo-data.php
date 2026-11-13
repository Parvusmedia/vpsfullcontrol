#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * Carga datos de demo (miembros, equipos, campañas con envíos) para enseñar el dashboard con métricas reales.
 * Uso: php deploy/seed-demo-data.php [--force]
 */
$root = dirname(__DIR__);
require_once $root . '/api/bootstrap.php';
require_once $root . '/api/_campaigns.php';

$force = in_array('--force', $argv ?? [], true);
$campaigns = ngaged_campaigns_store();
$existing = $campaigns['campaigns'] ?? [];
if (!$force && $existing !== []) {
    fwrite(STDERR, "Ya hay campañas. Usa --force para sobrescribir campañas y fusionar miembros demo.\n");
    exit(1);
}

$now = time();
$iso = static fn (int $offsetDays) => gmdate('c', $now - ($offsetDays * 86400));

$store = ngaged_members_store();
$teams = $store['teams'] ?? [];

$demoMembers = [
    ['id' => 'mem_demo_ana', 'name' => 'Ana García', 'email' => 'ana.garcia@demo.ngaged', 'teamId' => 'team_marketing', 'platformId' => 'linkedin-demo-ana'],
    ['id' => 'mem_demo_carlos', 'name' => 'Carlos Ruiz', 'email' => 'carlos.ruiz@demo.ngaged', 'teamId' => 'team_ventas', 'platformId' => 'linkedin-demo-carlos'],
    ['id' => 'mem_demo_laura', 'name' => 'Laura Méndez', 'email' => 'laura.mendez@demo.ngaged', 'teamId' => 'team_marketing', 'platformId' => 'linkedin-demo-laura'],
    ['id' => 'mem_demo_miguel', 'name' => 'Miguel Soto', 'email' => 'miguel.soto@demo.ngaged', 'teamId' => 'team_ventas', 'platformId' => 'linkedin-demo-miguel'],
    ['id' => 'mem_demo_elena', 'name' => 'Elena Vidal', 'email' => 'elena.vidal@demo.ngaged', 'teamId' => 'team_general', 'platformId' => 'linkedin-demo-elena'],
    ['id' => 'mem_demo_pablo', 'name' => 'Pablo Núñez', 'email' => 'pablo.nunez@demo.ngaged', 'teamId' => 'team_general', 'platformId' => ''],
];

$byEmail = [];
foreach ($store['members'] ?? [] as $m) {
    if (!is_array($m)) {
        continue;
    }
    $em = strtolower(trim((string) ($m['email'] ?? '')));
    if ($em !== '') {
        $byEmail[$em] = $m;
    }
}
foreach ($demoMembers as $dm) {
    $em = strtolower($dm['email']);
    $row = $byEmail[$em] ?? $dm;
    $row['id'] = $row['id'] ?? $dm['id'];
    $row['name'] = $dm['name'];
    $row['email'] = $em;
    $row['teamId'] = $dm['teamId'];
    if ($dm['platformId'] !== '' || empty($row['platformId'])) {
        $row['platformId'] = $dm['platformId'];
    }
    if (($row['platformId'] ?? '') !== '') {
        $row['connectStatus'] = 'active';
        $row['approvedAt'] = $row['approvedAt'] ?? gmdate('c');
        $row['linkedAt'] = $row['linkedAt'] ?? gmdate('c');
    } else {
        $row['connectStatus'] = 'pending';
    }
    $row['createdAt'] = $row['createdAt'] ?? gmdate('c');
    $byEmail[$em] = $row;
}
$store['members'] = array_values($byEmail);
$store['teams'] = $teams;
$store = ngaged_deduplicate_members_store($store)['store'];
ngaged_save_members($store);

function delivery(string $memberId, string $email, string $name, int $daysAgo, string $action): array
{
    $sent = gmdate('c', time() - ($daysAgo * 86400));
    $row = [
        'memberId' => $memberId,
        'email' => $email,
        'name' => $name,
        'sentAt' => $sent,
        'action' => $action === 'pending' ? '' : $action,
    ];
    if ($action === 'approve') {
        $action = 'repost';
        $row['action'] = 'repost';
    }
    if (in_array($action, ['repost', 'like', 'like_repost', 'decline'], true)) {
        $row['respondedAt'] = gmdate('c', time() - (($daysAgo - 1) * 86400));
    }
    return $row;
}

$camp1Deliveries = [
    delivery('mem_demo_ana', 'ana.garcia@demo.ngaged', 'Ana García', 5, 'like_repost'),
    delivery('mem_demo_carlos', 'carlos.ruiz@demo.ngaged', 'Carlos Ruiz', 5, 'repost'),
    delivery('mem_demo_laura', 'laura.mendez@demo.ngaged', 'Laura Méndez', 5, 'like'),
    delivery('mem_demo_miguel', 'miguel.soto@demo.ngaged', 'Miguel Soto', 5, 'decline'),
    delivery('mem_demo_elena', 'elena.vidal@demo.ngaged', 'Elena Vidal', 5, 'pending'),
    delivery('mem_demo_pablo', 'pablo.nunez@demo.ngaged', 'Pablo Núñez', 5, 'pending'),
];

$campaigns['campaigns'] = [
    [
        'id' => 'camp_demo_q4',
        'title' => 'Lanzamiento Q4',
        'linkedinUrl' => 'https://www.linkedin.com/feed/update/demo',
        'repostParentUrn' => 'urn:li:share:demo-q4',
        'commentary' => 'Comparte nuestro lanzamiento de trimestre.',
        'preview' => ['title' => 'Lanzamiento Q4', 'description' => 'Demo Ngaged', 'image' => ''],
        'memberIds' => array_column($demoMembers, 'id'),
        'createdAt' => $iso(6),
        'dispatchedAt' => $iso(5),
        'deliveries' => $camp1Deliveries,
    ],
    [
        'id' => 'camp_demo_case',
        'title' => 'Caso de éxito cliente',
        'linkedinUrl' => 'https://www.linkedin.com/feed/update/demo2',
        'repostParentUrn' => 'urn:li:share:demo-case',
        'commentary' => 'Historias reales de clientes.',
        'preview' => ['title' => 'Caso de éxito', 'description' => 'Demo Ngaged', 'image' => ''],
        'memberIds' => ['mem_demo_ana', 'mem_demo_laura', 'mem_demo_carlos'],
        'createdAt' => $iso(12),
        'dispatchedAt' => $iso(11),
        'deliveries' => [
            delivery('mem_demo_ana', 'ana.garcia@demo.ngaged', 'Ana García', 11, 'like_repost'),
            delivery('mem_demo_laura', 'laura.mendez@demo.ngaged', 'Laura Méndez', 11, 'like'),
            delivery('mem_demo_carlos', 'carlos.ruiz@demo.ngaged', 'Carlos Ruiz', 11, 'repost'),
        ],
    ],
];

ngaged_save_campaigns($campaigns);

echo "Demo seed OK: " . count($store['members']) . " miembros, " . count($campaigns['campaigns']) . " campañas.\n";
