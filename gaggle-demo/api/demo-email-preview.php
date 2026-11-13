<?php

declare(strict_types=1);

/**
 * HTML de ejemplo del email de campaña (público, solo demo / presentación).
 */
require_once __DIR__ . '/_mail.php';

$campaign = [
    'title' => 'Lanzamiento Q4',
    'commentary' => "Orgullosos de presentar nuestras novedades de trimestre.\n¡Comparte si encaja con tu red!",
    'preview' => [
        'title' => 'Lanzamiento Q4 — Lo que viene',
        'description' => 'Resumen en 2 minutos del anuncio de producto y del caso de éxito con un cliente europeo.',
        'image' => 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=560&h=280&fit=crop',
    ],
];

$member = [
    'name' => 'Ana García',
    'email' => 'ana.garcia@empresa.com',
];

$base = ngaged_app_base_url();
$demo = $base . '/demo/respuesta.html';
$urls = [
    'like' => $demo . '?v=like',
    'repost' => $demo . '?v=repost',
    'like_repost' => $demo . '?v=like_repost',
    'decline' => $demo . '?v=decline',
];

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: public, max-age=300');
header('X-Robots-Tag: noindex');
echo ngaged_campaign_email_html($campaign, $member, $urls);
