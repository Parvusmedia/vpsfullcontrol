<?php
declare(strict_types=1);

/**
 * One-off: enrich an export CSV with Icypeas work emails.
 * Usage (on prod host with icypeas.env):
 *   php enrich-csv-icypeas.php /path/to/export.csv [/path/to/out.csv]
 * Or by task id:
 *   php enrich-csv-icypeas.php --task=tsk_xxx [/path/to/out.csv]
 */

$docroot = getenv('CDE_DOCROOT') ?: '/var/www/vhosts/companydataenrichment.com/httpdocs';
require $docroot . '/api/_icypeas.php';
require $docroot . '/api/_tasks.php';

$taskId = '';
$inPath = '';
$outPath = '';

foreach ($argv as $i => $arg) {
    if ($i === 0) {
        continue;
    }
    if (str_starts_with($arg, '--task=')) {
        $taskId = trim(substr($arg, 7));
        continue;
    }
    if ($inPath === '') {
        $inPath = $arg;
    } elseif ($outPath === '') {
        $outPath = $arg;
    }
}

if ($taskId !== '') {
    $inPath = cde_tasks_csv_path($taskId);
}

if ($inPath === '' || !is_readable($inPath)) {
    fwrite(STDERR, "Input CSV not readable. Pass file path or --task=tsk_…\n");
    exit(1);
}

if ($outPath === '') {
    $outPath = preg_replace('/\.csv$/i', '', $inPath) . '-mail.csv';
}

if (!cde_icypeas_enabled()) {
    fwrite(STDERR, "Icypeas API key not configured.\n");
    exit(1);
}

$fh = fopen($inPath, 'rb');
if ($fh === false) {
    fwrite(STDERR, "Cannot open input.\n");
    exit(1);
}

$rawHead = fread($fh, 3);
if ($rawHead !== "\xEF\xBB\xBF") {
    rewind($fh);
} else {
    // already consumed BOM
}

$header = fgetcsv($fh);
if ($header === false) {
    fclose($fh);
    fwrite(STDERR, "Empty CSV.\n");
    exit(1);
}

$rows = [];
while (($cells = fgetcsv($fh)) !== false) {
    if ($cells === [null] || $cells === []) {
        continue;
    }
    $row = [];
    foreach ($header as $idx => $col) {
        $row[$col] = (string) ($cells[$idx] ?? '');
    }
    $rows[] = $row;
}
fclose($fh);

$total = count($rows);
fwrite(STDERR, "Enriching {$total} rows via Icypeas…\n");

$enriched = cde_icypeas_enrich_rows($rows);

$mailCols = cde_icypeas_csv_columns();
$outHeader = $header;
foreach ($mailCols as $col) {
    if (!in_array($col, $outHeader, true)) {
        $outHeader[] = $col;
    }
}

$out = fopen($outPath, 'wb');
if ($out === false) {
    fwrite(STDERR, "Cannot write output.\n");
    exit(1);
}
fwrite($out, "\xEF\xBB\xBF");
fputcsv($out, $outHeader);
$found = 0;
foreach ($enriched as $row) {
    $cells = [];
    foreach ($outHeader as $col) {
        $cells[] = cde_tasks_csv_normalize_cell((string) ($row[$col] ?? ''));
    }
    if (trim((string) ($row['work_email'] ?? '')) !== '') {
        $found++;
    }
    fputcsv($out, $cells);
}
fclose($out);

fwrite(STDERR, "Done. work_email found: {$found}/{$total}\n");
fwrite(STDERR, "Written: {$outPath}\n");
echo json_encode(['ok' => true, 'total' => $total, 'found' => $found, 'out' => $outPath], JSON_UNESCAPED_SLASHES) . "\n";
