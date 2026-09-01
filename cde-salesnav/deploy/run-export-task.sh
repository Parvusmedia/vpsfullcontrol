#!/bin/bash
set -euo pipefail

TASK_ID="${1:?task id required}"
DIR="$(cd "$(dirname "$0")" && pwd)"
DOCROOT="$(cd "$DIR/../../httpdocs" && pwd)"
PHP="${CDE_PHP_BIN:-/opt/plesk/php/8.3/bin/php}"

exec "$PHP" "$DOCROOT/api/salesnav-task-run.php" "$TASK_ID"
