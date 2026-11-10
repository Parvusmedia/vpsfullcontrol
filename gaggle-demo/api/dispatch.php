<?php

declare(strict_types=1);

require_once __DIR__ . '/_campaigns.php';
require_once __DIR__ . '/_mail.php';
require_once __DIR__ . '/_tokens.php';

gaggle_demo_cors();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gaggle_demo_json_response(405, ['ok' => false, 'error' => 'POST only']);
}

gaggle_demo_require_admin();
$input = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($input)) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'JSON inválido.']);
}

$campaignId = trim((string) ($input['campaignId'] ?? ''));
if ($campaignId === '') {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'campaignId required']);
}

$store = ngaged_campaigns_store();
$found = ngaged_find_campaign($store, $campaignId);
if ($found === null) {
    gaggle_demo_json_response(404, ['ok' => false, 'error' => 'Campaña no encontrada.']);
}

$idx = $found['index'];
$campaign = $found['campaign'];

if (!empty($campaign['dispatchedAt']) && empty($input['resend'])) {
    gaggle_demo_json_response(409, ['ok' => false, 'error' => 'La campaña ya fue enviada. Usa resend=true para reenviar.']);
}

$memberIds = $input['memberIds'] ?? $campaign['memberIds'] ?? [];
if (!is_array($memberIds)) {
    $memberIds = [];
}
$memberIds = array_values(array_unique(array_filter(array_map('strval', $memberIds))));
if ($memberIds === []) {
    gaggle_demo_json_response(400, ['ok' => false, 'error' => 'Elige al menos un miembro destino.']);
}
$campaign['memberIds'] = $memberIds;

$membersStore = ngaged_members_store();
$byId = [];
foreach ($membersStore['members'] ?? [] as $m) {
    if (is_array($m)) {
        $byId[(string) ($m['id'] ?? '')] = $m;
    }
}

$now = gmdate('c');
$deliveries = [];
$sent = 0;
$failed = [];

foreach ($memberIds as $mid) {
    $member = $byId[$mid] ?? null;
    if ($member === null) {
        $failed[] = ['memberId' => $mid, 'error' => 'Miembro no encontrado'];
        continue;
    }
    $email = (string) ($member['email'] ?? '');
    if ($email === '') {
        $failed[] = ['memberId' => $mid, 'error' => 'Sin email'];
        continue;
    }

    $token = ngaged_action_token($campaignId, $mid);
    $urls = [
        'like' => ngaged_action_url($token, 'like'),
        'repost' => ngaged_action_url($token, 'repost'),
        'like_repost' => ngaged_action_url($token, 'like_repost'),
        'decline' => ngaged_action_url($token, 'decline'),
    ];
    $subject = 'Ngaged · ' . ($campaign['title'] ?? 'Nueva campaña');
    $html = ngaged_campaign_email_html($campaign, $member, $urls);
    $ok = ngaged_send_mail($email, $subject, $html);

    $deliveries[] = [
        'memberId' => $mid,
        'email' => $email,
        'platformId' => (string) ($member['platformId'] ?? ''),
        'sentAt' => $now,
        'respondedAt' => null,
        'action' => null,
        'postGroupId' => null,
        'error' => $ok ? null : 'No se pudo enviar el email',
        'mailSent' => $ok,
    ];
    if ($ok) {
        $sent++;
    } else {
        $failed[] = ['memberId' => $mid, 'error' => 'mail() failed'];
    }
}

$campaign['deliveries'] = $deliveries;
$campaign['dispatchedAt'] = $now;
$campaign['status'] = 'dispatched';
$store['campaigns'][$idx] = $campaign;
ngaged_save_campaigns($store);

gaggle_demo_json_response(200, [
    'ok' => true,
    'sent' => $sent,
    'failed' => $failed,
    'campaign' => $campaign,
]);
