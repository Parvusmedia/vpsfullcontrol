#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * Crea o actualiza un administrador con permiso completo (admin).
 * Uso: php deploy/create-admin.php email@dominio.com 'ContraseñaLarga' [Nombre]
 */
$root = dirname(__DIR__);
require_once $root . '/api/bootstrap.php';
require_once $root . '/api/_admin_auth.php';

$email = strtolower(trim($argv[1] ?? ''));
$password = (string) ($argv[2] ?? '');
$name = trim($argv[3] ?? '') ?: 'Administrador';

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fwrite(STDERR, "Uso: php deploy/create-admin.php email contraseña [nombre]\n");
    exit(1);
}
if (strlen($password) < 10) {
    fwrite(STDERR, "La contraseña debe tener al menos 10 caracteres.\n");
    exit(1);
}

$store = ngaged_admins_store();
$found = ngaged_find_admin_by_email($store, $email);
if ($found !== null) {
    $idx = $found['index'];
    $row = $found['admin'];
    $row['passwordHash'] = password_hash($password, PASSWORD_DEFAULT);
    $row['role'] = 'admin';
    $row['active'] = true;
    $row['name'] = $name;
    $store['admins'][$idx] = $row;
    ngaged_save_admins($store);
    echo "Admin actualizado: {$email}\n";
    exit(0);
}

$store['admins'][] = [
    'id' => gaggle_demo_new_id('adm'),
    'email' => $email,
    'name' => $name,
    'passwordHash' => password_hash($password, PASSWORD_DEFAULT),
    'role' => 'admin',
    'active' => true,
    'createdAt' => gmdate('c'),
    'auth' => ['password' => true],
];
ngaged_save_admins($store);
echo "Admin creado (permiso completo): {$email}\n";
