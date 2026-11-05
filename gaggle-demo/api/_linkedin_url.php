<?php

declare(strict_types=1);

/**
 * Best-effort LinkedIn URL → URN for repost (activity or share).
 */
function ngaged_linkedin_url_to_urn(string $url): ?string
{
    $url = trim($url);
    if ($url === '') {
        return null;
    }

    if (preg_match('/^urn:li:(activity|share|ugcPost):[\dA-Za-z]+$/', $url)) {
        return $url;
    }

    if (preg_match('~urn:li:(activity|share|ugcPost):[\dA-Za-z]+~', $url, $m)) {
        return $m[0];
    }

    if (preg_match('~linkedin\.com/feed/update/(urn:li:[^/?]+)~i', $url, $m)) {
        return urldecode($m[1]);
    }

    if (preg_match('~-(activity|share)-(\d{10,})~i', $url, $m)) {
        $kind = strtolower($m[1]);
        $id = $m[2];
        return $kind === 'share' ? 'urn:li:share:' . $id : 'urn:li:activity:' . $id;
    }

    if (preg_match('~linkedin\.com/feed/update/[^/?]*?(\d{10,})~', $url, $m)) {
        return 'urn:li:activity:' . $m[1];
    }

    return null;
}

function ngaged_fetch_open_graph(string $url): array
{
    $out = ['title' => '', 'description' => '', 'image' => ''];
    if ($url === '' || !filter_var($url, FILTER_VALIDATE_URL)) {
        return $out;
    }

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; Ngaged/1.0)',
        CURLOPT_HTTPHEADER => ['Accept: text/html'],
    ]);
    $html = curl_exec($ch);
    curl_close($ch);

    if (!is_string($html) || $html === '') {
        return $out;
    }

    foreach (['og:title' => 'title', 'og:description' => 'description', 'og:image' => 'image'] as $prop => $key) {
        if (preg_match(
            '#<meta\s+(?:property|name)="' . preg_quote($prop, '#') . '"\s+content="([^"]*)"#i',
            $html,
            $m
        )) {
            $out[$key] = html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
        } elseif (preg_match(
            '#<meta\s+content="([^"]*)"\s+(?:property|name)="' . preg_quote($prop, '#') . '"#i',
            $html,
            $m
        )) {
            $out[$key] = html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
        }
    }

    return $out;
}
