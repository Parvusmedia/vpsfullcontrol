<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function gaggle_publora_company_workspace_id(): string
{
    $file = gaggle_demo_load_env();
    $id = trim((string) ($file['PUBLORA_WORKSPACE_ID'] ?? getenv('PUBLORA_WORKSPACE_ID') ?: ''));
    return strtolower($id);
}

/** UUID del cliente en Ngaged (externalOwner.companyId), no el accountId de Publora. */
function gaggle_publora_company_external_id(): string
{
    $file = gaggle_demo_load_env();
    $id = trim((string) (
        $file['PUBLORA_EXTERNAL_COMPANY_ID']
        ?? $file['PUBLORA_COMPANY_ID']
        ?? getenv('PUBLORA_EXTERNAL_COMPANY_ID')
        ?: getenv('PUBLORA_COMPANY_ID')
        ?: ''
    ));
    return strtolower($id);
}

function gaggle_publora_company_instance_id(): string
{
    $file = gaggle_demo_load_env();
    $id = trim((string) ($file['PUBLORA_INSTANCE_ID'] ?? 'ngaged'));
    return $id !== '' ? $id : 'ngaged';
}

/** Enlace de cliente del workspace (panel Publora), plan B si la API connection-link no está disponible. */
function gaggle_publora_client_connect_url(): string
{
    $file = gaggle_demo_load_env();
    $url = trim((string) (
        $file['PUBLORA_CLIENT_CONNECT_URL']
        ?? getenv('PUBLORA_CLIENT_CONNECT_URL')
        ?: ''
    ));
    if ($url !== '' && preg_match('#^https://app\.publora\.com/connect/[A-Za-z0-9_-]+$#', $url)) {
        return $url;
    }
    return '';
}

function gaggle_publora_company_configured(): bool
{
    return gaggle_publora_company_workspace_id() !== '' && gaggle_publora_company_external_id() !== '';
}

/**
 * @param array<string, string> $extraHeaders
 * @return array{ok:bool,http:int,error?:string,body?:array,data?:mixed,code?:string}
 */
function gaggle_publora_company_request(
    string $method,
    string $path,
    ?array $body = null,
    array $extraHeaders = []
): array {
    $apiKey = gaggle_demo_api_key();
    if ($apiKey === '') {
        return ['ok' => false, 'http' => 500, 'error' => 'PUBLORA_API_KEY not configured.'];
    }
    $workspaceId = gaggle_publora_company_workspace_id();
    if ($workspaceId === '') {
        return ['ok' => false, 'http' => 500, 'error' => 'PUBLORA_WORKSPACE_ID not configured.'];
    }

    $url = 'https://api.publora.com/api/v1/company/' . ltrim($path, '/');
    $headers = array_merge([
        'x-publora-key: ' . $apiKey,
        'x-publora-client: ngaged',
        'X-Publora-Workspace-Id: ' . $workspaceId,
        'Content-Type: application/json',
        'Accept: application/json',
    ], $extraHeaders);

    $ch = curl_init($url);
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
        return ['ok' => false, 'http' => $http, 'error' => 'Invalid JSON from Company API', 'raw' => substr($raw, 0, 500)];
    }

    if ($http >= 400 || ($decoded['success'] ?? true) === false) {
        $msg = (string) ($decoded['message'] ?? $decoded['error'] ?? ('HTTP ' . $http));
        return [
            'ok' => false,
            'http' => $http,
            'error' => $msg,
            'code' => isset($decoded['code']) ? (string) $decoded['code'] : null,
            'body' => $decoded,
        ];
    }

    return [
        'ok' => true,
        'http' => $http,
        'body' => $decoded,
        'data' => $decoded['data'] ?? $decoded,
    ];
}

function gaggle_publora_company_context_ok(): bool
{
    static $cache = null;
    if ($cache !== null) {
        return $cache;
    }
    if (!gaggle_publora_company_configured()) {
        $cache = false;
        return false;
    }
    $resp = gaggle_publora_company_request('GET', 'contexts/v2');
    if (!$resp['ok']) {
        $cache = false;
        return false;
    }
    $wantWs = gaggle_publora_company_workspace_id();
    $accounts = $resp['data']['accounts'] ?? [];
    if (!is_array($accounts)) {
        $cache = false;
        return false;
    }
    foreach ($accounts as $account) {
        if (!is_array($account)) {
            continue;
        }
        foreach ($account['workspaces'] ?? [] as $ws) {
            if (is_array($ws) && strtolower((string) ($ws['id'] ?? '')) === $wantWs) {
                $cache = true;
                return true;
            }
        }
    }
    $cache = false;
    return false;
}

/** Enlace OAuth LinkedIn para un empleado (Company API). */
function gaggle_publora_company_connection_link(string $credentialId): array
{
    $credentialId = strtolower(trim($credentialId));
    if (!preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/', $credentialId)) {
        return ['ok' => false, 'error' => 'credentialId inválido.'];
    }

    $resp = gaggle_publora_company_request('POST', 'connection-link', [
        'platform' => 'linkedin',
        'connectionSubtype' => 'personal',
        'externalOwner' => [
            'instanceId' => gaggle_publora_company_instance_id(),
            'companyId' => gaggle_publora_company_external_id(),
            'credentialId' => $credentialId,
        ],
    ]);

    if (!$resp['ok']) {
        return $resp;
    }

    $url = (string) (($resp['data']['url'] ?? $resp['data']['link'] ?? '') ?? '');
    if ($url === '') {
        return ['ok' => false, 'error' => 'Enlace de conexión vacío en la respuesta.'];
    }

    return ['ok' => true, 'url' => $url, 'data' => $resp['data']];
}

/** @return array{ok:bool,platformId?:string,connectionId?:string,error?:string} */
function gaggle_publora_company_linkedin_for_credential(string $credentialId): array
{
    $credentialId = strtolower(trim($credentialId));
    $companyId = gaggle_publora_company_external_id();
    $instanceId = gaggle_publora_company_instance_id();

    $resp = gaggle_publora_company_request('GET', 'connections');
    if (!$resp['ok']) {
        return $resp;
    }

    $items = $resp['data']['items'] ?? [];
    if (!is_array($items)) {
        $items = [];
    }

    foreach ($items as $row) {
        if (!is_array($row)) {
            continue;
        }
        $owners = $row['externalOwners'] ?? [];
        if (!is_array($owners)) {
            continue;
        }
        foreach ($owners as $owner) {
            if (!is_array($owner)) {
                continue;
            }
            if (
                ($owner['instanceId'] ?? '') === $instanceId
                && strtolower((string) ($owner['companyId'] ?? '')) === $companyId
                && strtolower((string) ($owner['credentialId'] ?? '')) === $credentialId
            ) {
                $platform = (string) ($row['platform'] ?? 'linkedin');
                $pid = (string) ($row['platformId'] ?? '');
                if ($pid === '') {
                    continue;
                }
                $channelKey = str_starts_with($pid, $platform . '-') ? $pid : ($platform . '-' . $pid);
                return [
                    'ok' => true,
                    'platformId' => $channelKey,
                    'connectionId' => (string) ($row['id'] ?? ''),
                ];
            }
        }
    }

    return ['ok' => false, 'error' => 'Aún no hay LinkedIn conectado para este empleado.'];
}

/**
 * Cuando el empleado usa el enlace de cliente del workspace (sin externalOwner por API).
 *
 * @return array{ok:bool,platformId?:string,connectionId?:string,error?:string}
 */
function gaggle_publora_company_linkedin_for_member_profile(array $member): array
{
    $resp = gaggle_publora_company_request('GET', 'connections');
    if (!$resp['ok']) {
        return $resp;
    }

    $items = $resp['data']['items'] ?? [];
    if (!is_array($items) || $items === []) {
        return ['ok' => false, 'error' => 'Aún no hay LinkedIn conectado para este empleado.'];
    }

    $email = strtolower(trim((string) ($member['email'] ?? '')));
    $name = strtolower(trim((string) ($member['name'] ?? '')));
    $local = $email !== '' && str_contains($email, '@') ? strstr($email, '@', true) : '';

    $linkedin = [];
    foreach ($items as $row) {
        if (!is_array($row)) {
            continue;
        }
        $platform = strtolower((string) ($row['platform'] ?? 'linkedin'));
        if ($platform !== 'linkedin') {
            continue;
        }
        $status = strtolower((string) ($row['status'] ?? 'active'));
        if ($status !== '' && !in_array($status, ['active', 'connected', 'ok'], true)) {
            continue;
        }
        $linkedin[] = $row;
    }

    if ($linkedin === []) {
        return ['ok' => false, 'error' => 'Aún no hay LinkedIn conectado en el workspace.'];
    }

    foreach ($linkedin as $row) {
        $username = strtolower((string) ($row['username'] ?? ''));
        $display = strtolower((string) ($row['displayName'] ?? ''));
        if ($email !== '' && ($username === $email || str_contains($username, $local))) {
            return gaggle_publora_company_row_to_channel($row);
        }
        if ($name !== '' && $display !== '' && str_contains($display, $name)) {
            return gaggle_publora_company_row_to_channel($row);
        }
    }

    if (count($linkedin) === 1) {
        return gaggle_publora_company_row_to_channel($linkedin[0]);
    }

    return [
        'ok' => false,
        'error' => 'Hay varios LinkedIn en el workspace. Tu administrador asignará tu canal en el panel Ngaged.',
    ];
}

/** @param array<string, mixed> $row */
function gaggle_publora_company_row_to_channel(array $row): array
{
    $platform = (string) ($row['platform'] ?? 'linkedin');
    $pid = (string) ($row['platformId'] ?? '');
    if ($pid === '') {
        return ['ok' => false, 'error' => 'Conexión sin identificador de canal.'];
    }
    $channelKey = str_starts_with($pid, $platform . '-') ? $pid : ($platform . '-' . $pid);

    return [
        'ok' => true,
        'platformId' => $channelKey,
        'connectionId' => (string) ($row['id'] ?? ''),
    ];
}

/** @return list<array{platformId:string,username:?string,displayName:?string,status:?string,source:string}> */
function gaggle_publora_company_list_channels(): array
{
    $resp = gaggle_publora_company_request('GET', 'connections');
    if (!$resp['ok']) {
        return [];
    }
    $items = $resp['data']['items'] ?? [];
    if (!is_array($items)) {
        return [];
    }
    $out = [];
    foreach ($items as $row) {
        if (!is_array($row)) {
            continue;
        }
        $mapped = gaggle_publora_company_row_to_channel($row);
        if (!$mapped['ok']) {
            continue;
        }
        $out[] = [
            'platformId' => $mapped['platformId'],
            'username' => isset($row['username']) ? (string) $row['username'] : null,
            'displayName' => isset($row['displayName']) ? (string) $row['displayName'] : null,
            'status' => isset($row['status']) ? (string) $row['status'] : null,
            'source' => 'workspace',
        ];
    }
    return $out;
}

function gaggle_publora_employee_connect_ready(): bool
{
    if (gaggle_publora_company_configured()) {
        if (gaggle_publora_company_context_ok()) {
            return true;
        }
    }
    if (gaggle_publora_client_connect_url() !== '') {
        return gaggle_demo_api_key() !== '';
    }

    return gaggle_publora_workspace_enabled();
}
