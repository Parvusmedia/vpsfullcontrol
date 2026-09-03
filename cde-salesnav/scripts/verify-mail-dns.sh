#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-companydataenrichment.com}"

check_txt() {
  local host="$1"
  local label="$2"
  local result
  result="$(dig +short TXT "$host" @8.8.8.8 2>/dev/null | tr -d '"' | paste -sd '' -)"
  if [[ -n "$result" ]]; then
    echo "OK   $label: ${result:0:80}..."
  else
    echo "MISSING $label ($host)"
  fi
}

echo "Mail DNS check for $DOMAIN (resolver 8.8.8.8)"
echo "-------------------------------------------"
check_txt "$DOMAIN" "SPF"
check_txt "_dmarc.$DOMAIN" "DMARC"
check_txt "default._domainkey.$DOMAIN" "DKIM"
check_txt "$DOMAIN" "TXT (all)"
echo "-------------------------------------------"
echo "DKIM + DMARC must be OK for good Gmail deliverability."
