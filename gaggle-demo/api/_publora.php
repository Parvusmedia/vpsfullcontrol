<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function gaggle_publora_request(string $method, string $path, ?array $body = null): array
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
        'x-publora-client: gaggle-demo',
    ];

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

function gaggle_publora_list_connections(): array
{
    $resp = gaggle_publora_request('GET', 'platform-connections');
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
