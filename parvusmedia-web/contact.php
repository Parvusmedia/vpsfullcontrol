<?php
/**
 * Contact form handler — sends to hello@parvusmedia.com
 * Includes math captcha verification + honeypot.
 */
declare(strict_types=1);

session_start();

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

require_once __DIR__ . '/lib/smtp_mail.php';

const CONTACT_TO = 'hello@parvusmedia.com';
const CAPTCHA_TTL = 600; // 10 minutes

function json_out(int $code, array $payload): void
{
    http_response_code($code);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

function captcha_secret(): string
{
    $path = __DIR__ . '/.captcha_secret';
    if (is_readable($path)) {
        $s = trim((string)file_get_contents($path));
        if ($s !== '') {
            return $s;
        }
    }
    // Fallback derived from server identity (still rotate via file if possible)
    return hash('sha256', __DIR__ . '|parvus-v2-captcha|' . (php_uname('n') ?: 'host'));
}

function make_captcha(): array
{
    $a = random_int(2, 12);
    $b = random_int(1, 9);
    $ops = ['+', '+', '-', '×'];
    $op = $ops[random_int(0, count($ops) - 1)];
    if ($op === '-') {
        if ($b > $a) {
            [$a, $b] = [$b, $a];
        }
        $answer = $a - $b;
        $question = "{$a} − {$b} = ?";
    } elseif ($op === '×') {
        $a = random_int(2, 9);
        $b = random_int(2, 9);
        $answer = $a * $b;
        $question = "{$a} × {$b} = ?";
    } else {
        $answer = $a + $b;
        $question = "{$a} + {$b} = ?";
    }

    $exp = time() + CAPTCHA_TTL;
    $payload = $answer . '|' . $exp . '|' . bin2hex(random_bytes(8));
    $token = hash_hmac('sha256', $payload, captcha_secret()) . '.' . base64_encode($payload);

    return [
        'ok' => true,
        'question' => $question,
        'token' => $token,
    ];
}

function verify_captcha(string $token, string $answerRaw): bool
{
    if ($token === '' || $answerRaw === '') {
        return false;
    }
    $parts = explode('.', $token, 2);
    if (count($parts) !== 2) {
        return false;
    }
    [$sig, $b64] = $parts;
    $payload = base64_decode($b64, true);
    if ($payload === false || $sig === '' || $payload === '') {
        return false;
    }
    $expected = hash_hmac('sha256', $payload, captcha_secret());
    if (!hash_equals($expected, $sig)) {
        return false;
    }
    $bits = explode('|', $payload);
    if (count($bits) < 2) {
        return false;
    }
    $answer = (int)$bits[0];
    $exp = (int)$bits[1];
    if ($exp < time()) {
        return false;
    }
    $given = preg_replace('/\s+/', '', $answerRaw);
    if ($given === null || $given === '' || !preg_match('/^-?\d+$/', $given)) {
        return false;
    }
    return (int)$given === $answer;
}

// Issue a new captcha challenge
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET' && (($_GET['action'] ?? '') === 'captcha')) {
    json_out(200, make_captcha());
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    json_out(405, ['ok' => false, 'error' => 'Method not allowed']);
}

// Honeypot
if (!empty($_POST['website'])) {
    json_out(200, ['ok' => true]);
}

$name = trim((string)($_POST['name'] ?? ''));
$email = trim((string)($_POST['email'] ?? ''));
$company = trim((string)($_POST['company'] ?? ''));
$interest = str_replace(["\r", "\n"], '', trim((string)($_POST['interest'] ?? '')));
$message = trim((string)($_POST['message'] ?? ''));
$consent = !empty($_POST['consent']);
$captchaAnswer = trim((string)($_POST['captcha'] ?? ''));
$captchaToken = trim((string)($_POST['captcha_token'] ?? ''));

if ($name === '' || $email === '' || $message === '' || !$consent) {
    json_out(400, ['ok' => false, 'error' => 'Missing required fields']);
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    json_out(400, ['ok' => false, 'error' => 'Invalid email']);
}

if (mb_strlen($name) > 120 || mb_strlen($email) > 160 || mb_strlen($company) > 160 || mb_strlen($interest) > 80 || mb_strlen($message) > 4000) {
    json_out(400, ['ok' => false, 'error' => 'Field too long']);
}

if (!verify_captcha($captchaToken, $captchaAnswer)) {
    json_out(400, [
        'ok' => false,
        'error' => 'Captcha failed',
        'captcha' => make_captcha(),
    ]);
}

$to = CONTACT_TO;
$subject = 'Parvus Media web inquiry' . ($interest !== '' ? ' — ' . $interest : '') . ($company !== '' ? ' — ' . $company : '');
$body = "Name: {$name}\nEmail: {$email}\nCompany: {$company}\nInterest: {$interest}\n\n{$message}\n\n--\nSent from parvusmedia.com\nIP: " . ($_SERVER['REMOTE_ADDR'] ?? '');

$sent = parvus_web_send_mail($to, $subject, $body, $email);

if (!$sent) {
    json_out(500, ['ok' => false, 'error' => 'Mail failed']);
}

json_out(200, ['ok' => true]);
