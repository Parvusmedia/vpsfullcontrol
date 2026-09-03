<?php
declare(strict_types=1);

require_once __DIR__ . '/_salesnav_admin.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Salesnav-Admin-Token');
    header('Access-Control-Allow-Credentials: true');
    http_response_code(204);
    exit;
}

header('Cache-Control: no-store');

$action = trim((string) ($_GET['action'] ?? ''));

if ($action === 'status' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    cde_json_response(200, [
        'ok' => true,
        'authenticated' => cde_sn_admin_session_valid() || cde_sn_admin_token_valid(trim((string) ($_SERVER['HTTP_X_SALESNAV_ADMIN_TOKEN'] ?? ''))),
        'admin_configured' => cde_sn_admin_configured(),
    ]);
}

if ($action === 'login' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!cde_sn_admin_configured()) {
        cde_json_response(503, ['ok' => false, 'error' => 'Admin access is not configured (SALESNAV_ADMIN_EMAILS).']);
    }
    $raw = file_get_contents('php://input') ?: '';
    $payload = json_decode($raw, true);
    if (!is_array($payload)) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
    }
    $email = trim((string) ($payload['email'] ?? ''));
    $password = trim((string) ($payload['password'] ?? $payload['token'] ?? ''));
    $ok = $email !== ''
        ? cde_sn_admin_login_with_panel($email, $password)
        : cde_sn_admin_login($password);
    if (!$ok) {
        cde_json_response(403, ['ok' => false, 'error' => 'Invalid email or password.']);
    }
    cde_json_response(200, [
        'ok' => true,
        'authenticated' => true,
        'email' => cde_customer_validate_email($email) ?? null,
    ]);
}

if ($action === 'logout' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    cde_sn_admin_logout();
    cde_json_response(200, ['ok' => true]);
}

cde_sn_admin_require_auth();

if ($action === 'overview' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    cde_json_response(200, ['ok' => true, 'overview' => cde_sn_admin_overview()]);
}

if ($action === 'users' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $q = strtolower(trim((string) ($_GET['q'] ?? '')));
    $users = cde_sn_admin_build_users_index();
    if ($q !== '') {
        $users = array_values(array_filter($users, static function (array $u) use ($q): bool {
            $email = strtolower((string) ($u['email'] ?? ''));
            $uid = strtolower((string) ($u['user_id'] ?? ''));

            return str_contains($email, $q) || str_contains($uid, $q);
        }));
    }
    cde_json_response(200, ['ok' => true, 'users' => $users]);
}

if ($action === 'user' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $userId = cde_sn_admin_resolve_user_id($_GET['user_id'] ?? '', $_GET['email'] ?? '');
    if ($userId === null) {
        cde_json_response(400, ['ok' => false, 'error' => 'user_id or email required']);
    }
    $detail = cde_sn_admin_user_detail($userId);
    if ($detail === null) {
        cde_json_response(404, ['ok' => false, 'error' => 'User not found']);
    }
    cde_json_response(200, ['ok' => true, 'detail' => $detail]);
}

if ($action === 'ledger' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $limit = (int) ($_GET['limit'] ?? 150);
    $userId = cde_sn_admin_resolve_user_id($_GET['user_id'] ?? '', $_GET['email'] ?? '');
    $kind = trim((string) ($_GET['kind'] ?? 'all'));
    cde_json_response(200, [
        'ok' => true,
        'ledger' => cde_sn_admin_read_ledger($limit, $userId, $kind === 'all' ? null : $kind),
    ]);
}

if ($action === 'tasks' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $limit = (int) ($_GET['limit'] ?? 100);
    $userId = cde_sn_admin_resolve_user_id($_GET['user_id'] ?? '', $_GET['email'] ?? '');
    $status = trim((string) ($_GET['status'] ?? 'all'));
    cde_json_response(200, [
        'ok' => true,
        'tasks' => cde_sn_admin_list_tasks($limit, $userId, $status === 'all' ? null : $status),
    ]);
}

if ($action === 'grant' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $raw = file_get_contents('php://input') ?: '';
    $payload = json_decode($raw, true);
    if (!is_array($payload)) {
        cde_json_response(400, ['ok' => false, 'error' => 'Invalid JSON body']);
    }
    $email = (string) ($payload['email'] ?? '');
    $amount = (int) ($payload['credits'] ?? $payload['amount'] ?? 0);
    $note = trim((string) ($payload['note'] ?? ''));
    $ref = trim((string) ($payload['ref'] ?? ''));
    $result = cde_sn_admin_grant_credits($email, $amount, $note, $ref);
    cde_json_response(200, $result);
}

cde_json_response(400, ['ok' => false, 'error' => 'Unknown action or method']);
