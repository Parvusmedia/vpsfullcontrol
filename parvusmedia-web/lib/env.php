<?php
declare(strict_types=1);

/**
 * Read KEY=value env files from the Plesk private tree (never from git).
 *
 * @return array<string, string>
 */
function parvus_web_read_env(string $filename): array
{
    static $cache = [];
    if (isset($cache[$filename])) {
        return $cache[$filename];
    }

    $candidates = [
        '/var/www/vhosts/parvusmedia.com/private/parvusmedia-web/' . $filename,
        '/var/www/vhosts/parvusmedia.com/private/cde/' . $filename,
        dirname(__DIR__) . '/private/' . $filename,
    ];

    $out = [];
    foreach ($candidates as $path) {
        if (!is_readable($path)) {
            continue;
        }
        $lines = file($path, FILE_IGNORE_NEW_LINES);
        if ($lines === false) {
            continue;
        }
        foreach ($lines as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                continue;
            }
            [$k, $v] = explode('=', $line, 2);
            $out[trim($k)] = trim($v, " \t\"'");
        }
        break;
    }

    $cache[$filename] = $out;
    return $out;
}
