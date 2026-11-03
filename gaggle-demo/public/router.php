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
