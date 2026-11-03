<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_teams.php';

gaggle_demo_cors();

gaggle_demo_require_admin();

$method = $_SERVER['REQUEST_METHOD'];
$store = ngaged_members_store();
$teams = $store['teams'] ?? [];

if ($method === 'GET') {
    gaggle_demo_json_response(200, ['ok' => true, 'teams' => $teams]);
}

$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    $input = [];
}

if ($method === 'POST') {
    $name = trim((string) ($input['name'] ?? ''));
    if ($name === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Nombre de equipo obligatorio.']);
    }
    foreach ($teams as $t) {
        if (is_array($t) && strcasecmp((string) ($t['name'] ?? ''), $name) === 0) {
            gaggle_demo_json_response(409, ['ok' => false, 'error' => 'Ya existe un equipo con ese nombre.']);
        }
    }
    $team = ['id' => gaggle_demo_new_id('team'), 'name' => $name];
    $teams[] = $team;
    $store['teams'] = $teams;
    ngaged_save_members($store);
    gaggle_demo_json_response(201, ['ok' => true, 'team' => $team, 'teams' => $teams]);
}

if ($method === 'PUT') {
    $id = trim((string) ($input['id'] ?? ''));
    $name = trim((string) ($input['name'] ?? ''));
    if ($id === '' || $name === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'id y name obligatorios.']);
    }
    $found = ngaged_find_team($store, $id);
    if ($found === null) {
        gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Equipo no encontrado.']);
    }
    $teams[$found['index']]['name'] = $name;
    $store['teams'] = $teams;
    ngaged_save_members($store);
    gaggle_demo_json_response(200, ['ok' => true, 'team' => $teams[$found['index']], 'teams' => $teams]);
}

if ($method === 'DELETE') {
    $id = trim((string) ($input['id'] ?? $_GET['id'] ?? ''));
    if ($id === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'id required']);
    }
    $teams = array_values(array_filter($teams, static fn ($t) => is_array($t) && ($t['id'] ?? '') !== $id));
    foreach ($store['members'] ?? [] as $i => $m) {
        if (is_array($m) && ($m['teamId'] ?? '') === $id) {
            $store['members'][$i]['teamId'] = '';
        }
    }
    $store['teams'] = $teams;
    ngaged_save_members($store);
    gaggle_demo_json_response(200, ['ok' => true, 'teams' => $teams]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
