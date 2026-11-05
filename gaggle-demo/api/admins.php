<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';

gaggle_demo_cors();

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET') {
    ngaged_require_owner();
    $store = ngaged_admins_store();
    $list = [];
    foreach ($store['admins'] as $a) {
        if (!is_array($a)) {
            continue;
        }
        $list[] = array_merge(ngaged_admin_public($a), [
            'active' => !empty($a['active']),
            'hasPassword' => ($a['passwordHash'] ?? '') !== '',
            'createdAt' => $a['createdAt'] ?? null,
        ]);
    }
    gaggle_demo_json_response(200, ['ok' => true, 'admins' => $list]);
}

if ($method === 'POST') {
    ngaged_require_owner();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }
    $email = strtolower(trim((string) ($input['email'] ?? '')));
    $name = trim((string) ($input['name'] ?? ''));
    $password = (string) ($input['password'] ?? '');
    $role = (string) ($input['role'] ?? 'admin');
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email válido obligatorio.']);
    }
    if (strlen($password) < 10) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'La contraseña debe tener al menos 10 caracteres.']);
    }
    if (!in_array($role, ['admin', 'owner'], true)) {
        $role = 'admin';
    }
    $store = ngaged_admins_store();
    if (ngaged_find_admin_by_email($store, $email) !== null) {
        gaggle_demo_json_response(409, ['ok' => false, 'error' => 'Ese email ya tiene acceso.']);
    }
    $row = [
        'id' => gaggle_demo_new_id('adm'),
        'email' => $email,
        'name' => $name !== '' ? $name : explode('@', $email)[0],
        'passwordHash' => password_hash($password, PASSWORD_DEFAULT),
        'role' => $role,
        'active' => true,
        'createdAt' => gmdate('c'),
        'auth' => ['password' => true],
    ];
    $store['admins'][] = $row;
    ngaged_save_admins($store);
    gaggle_demo_json_response(200, ['ok' => true, 'admin' => ngaged_admin_public($row)]);
}

if ($method === 'PUT') {
    ngaged_require_owner();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }
    $id = trim((string) ($input['id'] ?? ''));
    $store = ngaged_admins_store();
    $found = ngaged_find_admin_by_id($store, $id);
    if ($found === null) {
        gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Administrador no encontrado.']);
    }
    $idx = $found['index'];
    $row = $found['admin'];
    if (isset($input['active'])) {
        $row['active'] = (bool) $input['active'];
    }
    if (isset($input['name'])) {
        $row['name'] = trim((string) $input['name']);
    }
    $newPass = (string) ($input['password'] ?? '');
    if ($newPass !== '') {
        if (strlen($newPass) < 10) {
            gaggle_demo_json_response(400, ['ok' => false, 'error' => 'La contraseña debe tener al menos 10 caracteres.']);
        }
        $row['passwordHash'] = password_hash($newPass, PASSWORD_DEFAULT);
    }
    $store['admins'][$idx] = $row;
    ngaged_save_admins($store);
    gaggle_demo_json_response(200, ['ok' => true, 'admin' => ngaged_admin_public($row)]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
