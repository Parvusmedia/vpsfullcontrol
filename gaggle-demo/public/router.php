<?php

declare(strict_types=1);

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

if (str_starts_with($uri, '/api/')) {
    $script = basename($uri);
    $map = [
        'health' => 'health.php',
        'connections' => 'connections.php',
        'activities' => 'activities.php',
        'respond' => 'respond.php',
        'campaigns' => 'campaigns.php',
        'members' => 'members.php',
        'preview-post' => 'preview-post.php',
        'dispatch' => 'dispatch.php',
        'action' => 'action.php',
        'stats' => 'stats.php',
        'campaign-detail' => 'campaign-detail.php',
        'member-queue' => 'member-queue.php',
        'member-respond' => 'member-respond.php',
    ];
    if (isset($map[$script])) {
        require dirname(__DIR__) . '/api/' . $map[$script];
        return true;
    }
    http_response_code(404);
    header('Content-Type: application/json');
    echo json_encode(['ok' => false, 'error' => 'Unknown API route']);
    return true;
}

if ($uri === '/go' || $uri === '/go/') {
    header('Content-Type: text/html; charset=utf-8');
    readfile(__DIR__ . '/go.html');
    return true;
}

$file = __DIR__ . $uri;
if ($uri !== '/' && is_file($file)) {
    return false;
}

$index = __DIR__ . '/index.html';
if (is_file($index)) {
    header('Content-Type: text/html; charset=utf-8');
    readfile($index);
    return true;
}

http_response_code(404);
echo 'Not found';
return true;
