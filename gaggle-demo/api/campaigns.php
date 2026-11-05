<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_linkedin_url.php';

gaggle_demo_cors();
ngaged_maybe_migrate_legacy();

$method = $_SERVER['REQUEST_METHOD'];
$store = ngaged_campaigns_store();

if ($method === 'GET') {
    gaggle_demo_require_admin();
    $campaigns = $store['campaigns'] ?? [];
    if (!is_array($campaigns)) {
        $campaigns = [];
    }
    usort($campaigns, static fn ($a, $b) => strcmp((string) ($b['createdAt'] ?? ''), (string) ($a['createdAt'] ?? '')));
    gaggle_demo_json_response(200, ['ok' => true, 'campaigns' => $campaigns]);
}

if ($method === 'POST') {
    gaggle_demo_require_admin();
    $input = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($input)) {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
    }

    $title = trim((string) ($input['title'] ?? ''));
    if ($title === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'El título es obligatorio.']);
    }

    $linkedinUrl = trim((string) ($input['linkedinUrl'] ?? ''));
    $urn = trim((string) ($input['repostParentUrn'] ?? ''));
    if ($urn === '' && $linkedinUrl !== '') {
        $parsed = ngaged_linkedin_url_to_urn($linkedinUrl);
        if ($parsed !== null) {
            $urn = $parsed;
        }
    }
    if ($urn === '') {
        gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Indica una URL de LinkedIn o un URN válido.']);
    }

    $preview = $input['preview'] ?? [];
    if (!is_array($preview)) {
        $preview = [];
    }

    $memberIds = $input['memberIds'] ?? [];
    if (!is_array($memberIds)) {
        $memberIds = [];
    }
    $memberIds = array_values(array_unique(array_filter(array_map('strval', $memberIds))));

    $sendNow = !empty($input['sendNow']);

    $campaign = [
        'id' => gaggle_demo_new_id('camp'),
        'title' => $title,
        'linkedinUrl' => $linkedinUrl,
        'repostParentUrn' => $urn,
        'commentary' => trim((string) ($input['commentary'] ?? '')),
        'preview' => [
            'title' => trim((string) ($preview['title'] ?? $title)),
            'description' => trim((string) ($preview['description'] ?? '')),
            'image' => trim((string) ($preview['image'] ?? '')),
        ],
        'memberIds' => $memberIds,
        'createdAt' => gmdate('c'),
        'dispatchedAt' => null,
        'status' => 'draft',
        'deliveries' => [],
    ];

    $campaigns = $store['campaigns'] ?? [];
    if (!is_array($campaigns)) {
        $campaigns = [];
    }
    $campaigns[] = $campaign;
    ngaged_save_campaigns(['campaigns' => $campaigns]);

    gaggle_demo_json_response(201, ['ok' => true, 'campaign' => $campaign, 'sendNow' => $sendNow]);
}

gaggle_demo_json_response(405, ['ok' => false, 'error' => 'Method not allowed']);
