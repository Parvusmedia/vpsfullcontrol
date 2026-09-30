<?php
declare(strict_types=1);

require_once __DIR__ . '/env.php';

/**
 * POST contact lead to n8n (best-effort; never throws).
 */
function parvus_notify_contact_n8n(string $email, string $pageUrl): void
{
    $env = parvus_web_read_env('n8n-contact.env');
    $url = trim($env['N8N_CONTACT_WEBHOOK_URL'] ?? '');
    if ($url === '' || !filter_var($url, FILTER_VALIDATE_URL)) {
        return;
    }

    $payload = json_encode(
        ['email' => $email, 'url' => $pageUrl],
        JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR
    );

    $ctx = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/json\r\nAccept: application/json\r\n",
            'content' => $payload,
            'timeout' => 4,
            'ignore_errors' => true,
        ],
    ]);

    try {
        @file_get_contents($url, false, $ctx);
    } catch (Throwable $e) {
        // ignore
    }
}
