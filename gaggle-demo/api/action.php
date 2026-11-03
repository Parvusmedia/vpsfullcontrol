<?php

declare(strict_types=1);

require_once __DIR__ . '/_tokens.php';
require_once __DIR__ . '/_actions.php';

gaggle_demo_cors();

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $token = trim((string) ($_GET['token'] ?? ''));
    $action = trim((string) ($_GET['action'] ?? ''));
    $verified = ngaged_verify_action_token($token);
    if ($verified === null) {
        gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
    }
    if ($action === '' || !in_array($action, ['approve', 'decline'], true)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Indica action=approve o decline']);
    }
    $result = ngaged_apply_campaign_action($verified['campaignId'], $verified['memberId'], $action);
    if (!$result['ok']) {
        gaggle_demo_json_response(422, ['ok' => false, 'error' => $result['error'] ?? 'Error']);
    }
    gaggle_demo_json_response(200, [
        'ok' => true,
        'action' => $action,
        'message' => $action === 'approve'
            ? '¡Gracias! Tu repost se ha publicado en LinkedIn.'
            : 'Entendido. Has ignorado esta campaña.',
    ]);
}

if ($method === 'POST') {
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }
    $token = trim((string) ($input['token'] ?? ''));
    $action = trim((string) ($input['action'] ?? ''));
    $verified = ngaged_verify_action_token($token);
    if ($verified === null) {
        gaggle_demo_json_response(401, ['ok' => false, 'error' => 'Enlace caducado o no válido.']);
    }
    $result = ngaged_apply_campaign_action($verified['campaignId'], $verified['memberId'], $action);
    if (!$result['ok']) {
        gaggle_demo_json_response(422, ['ok' => false, 'error' => $result['error'] ?? 'Error']);
    }
    gaggle_demo_json_response(200, [
        'ok' => true,
        'action' => $action,
        'delivery' => $result['delivery'] ?? null,
    ]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
