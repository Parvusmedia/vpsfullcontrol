#!/usr/bin/env bash
# Run on parvus-vps: point digitanimal.pmediaplus.com → 87.106.194.137 via Plesk on nextconvers.
set -euo pipefail
export DNS_HOST=digitanimal
export DNS_DOMAIN=pmediaplus.com
export DNS_IP="${DNS_IP:-87.106.194.137}"
bash /opt/apps/education-ai-advisor/scripts/plesk-add-a-record.sh
