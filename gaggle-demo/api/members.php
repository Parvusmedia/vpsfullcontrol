<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_teams.php';

gaggle_demo_cors();

$method = $_SERVER['REQUEST_METHOD'];
$store = ngaged_members_store();
$members = $store['members'] ?? [];
if (!is_array($members)) {
    $members = [];
}

if ($method === 'GET') {
    gaggle_demo_require_admin();
    $deduped = ngaged_deduplicate_members_store($store);
    if ($deduped['removed'] > 0) {
        ngaged_save_members($deduped['store']);
        $store = $deduped['store'];
        $members = $store['members'] ?? [];
    }
    gaggle_demo_json_response(200, [
        'ok' => true,
        'members' => $members,
        'teams' => $store['teams'] ?? [],
        'dedupedRemoved' => $deduped['removed'],
    ]);
}

if ($method === 'POST') {
    gaggle_demo_require_full_admin();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }

    $email = strtolower(trim((string) ($input['email'] ?? '')));
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email válido obligatorio.']);
    }

    foreach ($members as $m) {
        if (is_array($m) && strtolower((string) ($m['email'] ?? '')) === $email) {
            gaggle_demo_json_response(409, ['ok' => false, 'error' => 'Ese email ya está registrado.']);
        }
    }

    $teamId = trim((string) ($input['teamId'] ?? ''));
    if ($teamId !== '' && ngaged_find_team($store, $teamId) === null) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Equipo no válido.']);
    }

    $member = [
        'id' => gaggle_demo_new_id('mem'),
        'name' => trim((string) ($input['name'] ?? '')),
        'email' => $email,
        'platformId' => trim((string) ($input['platformId'] ?? '')),
        'teamId' => $teamId,
        'createdAt' => gmdate('c'),
    ];

    $members[] = $member;
    $store['members'] = $members;
    ngaged_save_members($store);
    gaggle_demo_json_response(201, ['ok' => true, 'member' => $member]);
}

if ($method === 'DELETE') {
    gaggle_demo_require_full_admin();
    $input = json_decode((string) file_get_contents('php://input'), true);
    $id = trim((string) ($input['id'] ?? $_GET['id'] ?? ''));
    if ($id === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'id required']);
    }
    $members = array_values(array_filter($members, static fn ($m) => is_array($m) && ($m['id'] ?? '') !== $id));
    $store['members'] = $members;
    ngaged_save_members($store);
    gaggle_demo_json_response(200, ['ok' => true]);
}

if ($method === 'PUT') {
    gaggle_demo_require_full_admin();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }
    $id = trim((string) ($input['id'] ?? ''));
    $found = ngaged_find_member(['members' => $members], $id);
    if ($found === null) {
        gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Miembro no encontrado.']);
    }
    $i = $found['index'];
    $members[$i]['name'] = trim((string) ($input['name'] ?? $members[$i]['name'] ?? ''));
    $members[$i]['email'] = strtolower(trim((string) ($input['email'] ?? $members[$i]['email'] ?? '')));
    $members[$i]['platformId'] = trim((string) ($input['platformId'] ?? $members[$i]['platformId'] ?? ''));
    if (array_key_exists('teamId', $input)) {
        $teamId = trim((string) ($input['teamId'] ?? ''));
        if ($teamId !== '' && ngaged_find_team(['teams' => $store['teams'] ?? []], $teamId) === null) {
            gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Equipo no válido.']);
        }
        $members[$i]['teamId'] = $teamId;
    }
    if ($members[$i]['platformId'] !== '') {
        $members[$i]['connectStatus'] = 'linked';
        $members[$i]['linkedAt'] = gmdate('c');
    }
    $store['members'] = $members;
    ngaged_save_members($store);
    gaggle_demo_json_response(200, ['ok' => true, 'member' => $members[$i]]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
