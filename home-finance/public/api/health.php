<?php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';

$configured = hf_api_token() !== '';
$dataOk = is_dir(hf_data_dir()) || is_writable(dirname(hf_data_dir()));

echo json_encode([
    'ok' => true,
    'configured' => $configured,
    'data_dir_writable' => $dataOk,
]);
