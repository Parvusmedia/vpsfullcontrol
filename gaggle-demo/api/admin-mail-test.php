<?php

declare(strict_types=1);

require_once __DIR__ . '/_admin_auth.php';
require_once __DIR__ . '/_mail.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

ngaged_require_admin_access();
$admin = ngaged_current_admin();
if ($admin === null) {
    gaggle_demo_json_response(403, ['ok' => false, 'error' => 'Sesión requerida']);
}

$to = strtolower(trim((string) ($admin['email'] ?? '')));
if ($to === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Email de admin no disponible.']);
}

$html = '<p>Prueba de correo Ngaged (' . htmlspecialchars(ngaged_mail_transport_label(), ENT_QUOTES) . ').</p>';
$result = ngaged_send_mail_verbose($to, 'Ngaged · prueba de correo', $html, 'Prueba de correo Ngaged.');
if (!$result['ok']) {
    gaggle_demo_json_response(502, ['ok' => false, 'error' => $result['error'] ?? 'Envío fallido', 'transport' => $result['transport']]);
}

gaggle_demo_json_response(200, ['ok' => true, 'transport' => $result['transport'], 'to' => $to]);
