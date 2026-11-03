<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function gaggle_publora_request(string $method, string $path, ?array $body = null, ?string $publoraUserId = null): array
{
    $apiKey = gaggle_demo_api_key();
    if ($apiKey === '') {
        return ['ok' => false, 'http' => 500, 'error' => 'PUBLORA_API_KEY not configured.'];
    }

    $url = 'https://api.publora.com/api/v1/' . ltrim($path, '/');
    $ch = curl_init($url);
    $headers = [
        'x-publora-key: ' . $apiKey,
        'Content-Type: application/json',
        'Accept: application/json',
        'x-publora-client: ngaged',
    ];
    if ($publoraUserId !== null && $publoraUserId !== '') {
        $headers[] = 'x-publora-user-id: ' . $publoraUserId;
    }

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => strtoupper($method),
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => 60,
    ]);

    if ($body !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    }

    $raw = curl_exec($ch);
    $http = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        return ['ok' => false, 'http' => 0, 'error' => $err ?: 'curl failed'];
    }

    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        return ['ok' => false, 'http' => $http, 'error' => 'Invalid JSON from Publora', 'raw' => substr($raw, 0, 500)];
    }

    if ($http >= 400) {
        $msg = $decoded['error'] ?? $decoded['message'] ?? ('HTTP ' . $http);
        return ['ok' => false, 'http' => $http, 'error' => is_string($msg) ? $msg : json_encode($msg), 'body' => $decoded];
    }

    return ['ok' => true, 'http' => $http, 'body' => $decoded];
}

function gaggle_publora_list_connections(?string $publoraUserId = null): array
{
    $resp = gaggle_publora_request('GET', 'platform-connections', null, $publoraUserId);
    if (!$resp['ok']) {
        return $resp;
    }
    $body = $resp['body'];
    $list = $body['connections'] ?? $body['platforms'] ?? $body;
    if (!is_array($list)) {
        $list = [];
    }
    return ['ok' => true, 'connections' => $list];
}

function gaggle_publora_publish_activity(array $activity, string $platformId): array
{
    $payload = [
        'platforms' => [$platformId],
        'publishNow' => true,
    ];

    $type = (string) ($activity['type'] ?? 'post');
    $content = trim((string) ($activity['content'] ?? ''));

    if ($type === 'repost') {
        $urn = trim((string) ($activity['repostParentUrn'] ?? ''));
        if ($urn === '') {
            return ['ok' => false, 'error' => 'Missing repostParentUrn on activity.'];
        }
        $payload['content'] = $content;
        $payload['platformSettings'] = [
            'linkedin' => [
                'repostParentUrn' => $urn,
                'repostVisibility' => 'PUBLIC',
            ],
        ];
    } else {
        if ($content === '') {
            return ['ok' => false, 'error' => 'Post content is empty.'];
        }
        $payload['content'] = $content;
    }

    $resp = gaggle_publora_request('POST', 'create-post', $payload);
    if (!$resp['ok']) {
        return $resp;
    }
    return [
        'ok' => true,
        'postGroupId' => $resp['body']['postGroupId'] ?? null,
        'scheduledTime' => $resp['body']['scheduledTime'] ?? null,
        'publora' => $resp['body'],
    ];
}

function gaggle_publora_linkedin_reshare(string $platformId, string $repostParentUrn, string $commentary = ''): array
{
    $urn = trim($repostParentUrn);
    if ($urn === '') {
        return ['ok' => false, 'error' => 'Missing repost URN.'];
    }

    $payload = [
        'platforms' => [$platformId],
        'publishNow' => true,
        'repostParentUrn' => $urn,
        'repostVisibility' => 'PUBLIC',
    ];
    if (trim($commentary) !== '') {
        $payload['content'] = trim($commentary);
    }

    $resp = gaggle_publora_request('POST', 'linkedin-reshare', $payload);
    if (!$resp['ok'] && ($resp['http'] ?? 0) === 404) {
        $fallback = [
            'platforms' => [$platformId],
            'publishNow' => true,
            'content' => trim($commentary) !== '' ? trim($commentary) : ' ',
            'platformSettings' => [
                'linkedin' => [
                    'repostParentUrn' => $urn,
                    'repostVisibility' => 'PUBLIC',
                ],
            ],
        ];
        $resp = gaggle_publora_request('POST', 'create-post', $fallback);
    }

    if (!$resp['ok']) {
        return $resp;
    }

    return [
        'ok' => true,
        'postGroupId' => $resp['body']['postGroupId'] ?? null,
        'scheduledTime' => $resp['body']['scheduledTime'] ?? null,
    ];
}

function gaggle_publora_list_posts(int $limit = 20): array
{
    $resp = gaggle_publora_request('GET', 'posts?limit=' . max(1, min(50, $limit)));
    if (!$resp['ok']) {
        return $resp;
    }
    $posts = $resp['body']['posts'] ?? $resp['body']['data'] ?? $resp['body'];
    if (!is_array($posts)) {
        $posts = [];
    }
    return ['ok' => true, 'posts' => $posts];
}

function gaggle_publora_workspace_enabled(): bool
{
    static $cache = null;
    if ($cache !== null) {
        return $cache;
    }
    $resp = gaggle_publora_request('GET', 'workspace/users?limit=1');
    if (!$resp['ok'] && str_contains((string) ($resp['error'] ?? ''), 'Workspace access is not enabled')) {
        $cache = false;
        return false;
    }
    $cache = $resp['ok'];
    return $cache;
}

function gaggle_publora_create_managed_user(string $email, string $displayName): array
{
    $resp = gaggle_publora_request('POST', 'workspace/users', [
        'username' => $email,
        'displayName' => $displayName !== '' ? $displayName : $email,
    ]);
    if (!$resp['ok']) {
        return $resp;
    }
    $user = $resp['body']['user'] ?? $resp['body'];
    $id = is_array($user) ? (string) ($user['_id'] ?? $user['id'] ?? '') : '';
    if ($id === '') {
        return ['ok' => false, 'error' => 'Managed user created but ID missing.'];
    }
    return ['ok' => true, 'userId' => $id, 'user' => $user];
}

function gaggle_publora_connection_url(string $publoraUserId, int $expiresInDays = 30): array
{
    $resp = gaggle_publora_request(
        'POST',
        'workspace/users/' . rawurlencode($publoraUserId) . '/connection-url',
        ['expiresInDays' => max(1, min(90, $expiresInDays)), 'rotate' => true]
    );
    if (!$resp['ok']) {
        return $resp;
    }
    return [
        'ok' => true,
        'url' => (string) ($resp['body']['url'] ?? ''),
        'tokenExpiresAt' => $resp['body']['tokenExpiresAt'] ?? null,
    ];
}

/** @return array{ok:bool,platformId?:string,connections?:array} */
function gaggle_publora_first_linkedin_for_user(string $publoraUserId): array
{
    $resp = gaggle_publora_list_connections($publoraUserId);
    if (!$resp['ok']) {
        return $resp;
    }
    foreach ($resp['connections'] as $row) {
        if (!is_array($row)) {
            continue;
        }
        $pid = (string) ($row['platformId'] ?? '');
        if (str_starts_with($pid, 'linkedin-')) {
            return ['ok' => true, 'platformId' => $pid, 'connections' => $resp['connections']];
        }
    }
    return ['ok' => false, 'error' => 'Aún no hay LinkedIn conectado para este usuario.'];
}
