<?php

declare(strict_types=1);

require_once __DIR__ . '/_linkedin_url.php';
require_once __DIR__ . '/_publora.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_admin();
$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$url = trim((string) ($input['url'] ?? ''));
$urnOverride = trim((string) ($input['repostParentUrn'] ?? ''));
$urn = $urnOverride !== '' ? $urnOverride : ($url !== '' ? (ngaged_linkedin_url_to_urn($url) ?? '') : '');

$preview = [
    'title' => trim((string) ($input['title'] ?? '')),
    'description' => trim((string) ($input['description'] ?? '')),
    'image' => trim((string) ($input['image'] ?? '')),
];

if ($url !== '' && ($preview['title'] === '' || $preview['description'] === '')) {
    $og = ngaged_fetch_open_graph($url);
    if ($preview['title'] === '') {
        $preview['title'] = $og['title'];
    }
    if ($preview['description'] === '') {
        $preview['description'] = $og['description'];
    }
    if ($preview['image'] === '') {
        $preview['image'] = $og['image'];
    }
}

$matchedPost = null;
if ($urn !== '') {
    $postsResp = gaggle_publora_list_posts(30);
    if ($postsResp['ok']) {
        foreach ($postsResp['posts'] as $post) {
            if (!is_array($post)) {
                continue;
            }
            $content = json_encode($post);
            if ($content !== false && str_contains($content, $urn)) {
                $matchedPost = $post;
                if ($preview['title'] === '') {
                    $preview['title'] = trim((string) ($post['content'] ?? $post['text'] ?? ''));
                    if (strlen($preview['title']) > 120) {
                        $preview['title'] = substr($preview['title'], 0, 117) . '…';
                    }
                }
                break;
            }
        }
    }
}

if ($urn === '' && $url !== '') {
    gaggle_demo_json_response(422, [
        'ok' => false,
        'error' => 'No pudimos obtener el URN desde la URL. Pégalo manualmente.',
        'preview' => $preview,
    ]);
}

gaggle_demo_json_response(200, [
    'ok' => true,
    'repostParentUrn' => $urn,
    'preview' => $preview,
    'matchedOwnPost' => $matchedPost !== null,
]);
