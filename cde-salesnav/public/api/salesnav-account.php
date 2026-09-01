<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
require __DIR__ . '/_customers.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cde_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = [];
}

$action = strtolower(trim((string) ($payload['action'] ?? 'signin')));
$email = cde_customer_normalize_email((string) ($payload['email'] ?? ''));
$password = (string) ($payload['password'] ?? '');
$passwordConfirm = (string) ($payload['password_confirm'] ?? $payload['passwordConfirm'] ?? '');
$token = trim((string) ($payload['token'] ?? ''));

if ($action === 'signout') {
    cde_salesnav_sign_out_customer();
    cde_json_response(200, [
        'ok' => true,
        'signed_out' => true,
        'balance' => 0,
        'email' => '',
    ]);
}

if ($action === 'verify') {
    $result = cde_customer_verify_token($token);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Verification failed.',
            'code' => $result['code'] ?? 'invalid_token',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'verified' => true,
        'email' => $result['email'] ?? '',
        'balance' => (int) ($result['balance'] ?? 0),
    ]);
}

if ($action === 'register') {
    $result = cde_customer_register($email, $password, $passwordConfirm);
    if (!$result['ok']) {
        $status = ($result['code'] ?? '') === 'email_exists' ? 409 : 400;
        cde_json_response($status, [
            'ok' => false,
            'error' => $result['error'] ?? 'Registration failed.',
            'code' => $result['code'] ?? 'register_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'email' => $result['email'] ?? $email,
        'needs_verification' => !empty($result['needs_verification']),
        'message' => !empty($result['needs_verification'])
            ? 'Check your inbox to confirm your email before signing in.'
            : 'Account created. You can sign in now.',
    ]);
}

if ($action === 'resend') {
    if ($email === '') {
        cde_json_response(400, ['ok' => false, 'error' => 'Email is required.']);
    }
    $result = cde_customer_resend_verification($email);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Could not resend email.',
            'code' => $result['code'] ?? 'resend_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'message' => 'If an unconfirmed account exists for this email, we sent a new confirmation link.',
    ]);
}

if ($action === 'continue') {
    $result = cde_customer_continue($email);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Could not continue.',
            'code' => $result['code'] ?? 'continue_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'next_step' => $result['next_step'] ?? 'setup',
        'email' => $result['email'] ?? $email,
        'balance' => (int) ($result['balance'] ?? 0),
    ]);
}

if ($action === 'legacy_signin') {
    $result = cde_customer_legacy_sign_in($email);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Could not sign in.',
            'code' => $result['code'] ?? 'legacy_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'email' => $result['email'] ?? $email,
        'balance' => (int) ($result['balance'] ?? 0),
        'has_credits' => ((int) ($result['balance'] ?? 0)) > 0,
    ]);
}

if ($action === 'forgot') {
    if ($email === '') {
        cde_json_response(400, ['ok' => false, 'error' => 'Email is required.']);
    }
    $result = cde_customer_forgot_password($email);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Could not send reset email.',
            'code' => $result['code'] ?? 'forgot_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'message' => $result['message'] ?? 'If an account exists for this email, we sent reset instructions.',
    ]);
}

if ($action === 'reset') {
    $result = cde_customer_reset_password($token, $password, $passwordConfirm);
    if (!$result['ok']) {
        cde_json_response(400, [
            'ok' => false,
            'error' => $result['error'] ?? 'Could not reset password.',
            'code' => $result['code'] ?? 'reset_failed',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'email' => $result['email'] ?? '',
        'balance' => (int) ($result['balance'] ?? 0),
        'has_credits' => ((int) ($result['balance'] ?? 0)) > 0,
    ]);
}

if ($action === 'signin') {
    $result = cde_customer_sign_in($email, $password);
    if (!$result['ok']) {
        $status = ($result['code'] ?? '') === 'needs_verification' ? 403 : 401;
        cde_json_response($status, [
            'ok' => false,
            'error' => $result['error'] ?? 'Sign in failed.',
            'code' => $result['code'] ?? 'signin_failed',
            'needs_verification' => ($result['code'] ?? '') === 'needs_verification',
        ]);
    }
    cde_json_response(200, [
        'ok' => true,
        'email' => $result['email'] ?? $email,
        'balance' => (int) ($result['balance'] ?? 0),
        'has_credits' => ((int) ($result['balance'] ?? 0)) > 0,
    ]);
}

cde_json_response(400, ['ok' => false, 'error' => 'Unknown action.']);
