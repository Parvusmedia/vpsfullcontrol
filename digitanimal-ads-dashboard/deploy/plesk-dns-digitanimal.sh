#!/usr/bin/env bash
# Run on parvus-vps: point digitanimal.pmediaplus.com → 87.106.194.137 via Plesk on nextconvers.
set -euo pipefail
export DNS_HOST=digitanimal
export DNS_DOMAIN=pmediaplus.com
export DNS_IP="${DNS_IP:-87.106.194.137}"
OLD_IP="${OLD_LANDING_IP:-82.223.3.205}"

bash /opt/apps/education-ai-advisor/scripts/plesk-add-a-record.sh

ssh -i "${HOME}/.ssh/nextconvers_vps_ed25519" -o BatchMode=yes root@82.223.3.205 \
  "plesk bin dns -d ${DNS_DOMAIN} -a ${DNS_HOST} -ip ${OLD_IP}" 2>/dev/null \
  || echo "(old A ${OLD_IP} already removed or absent)"
