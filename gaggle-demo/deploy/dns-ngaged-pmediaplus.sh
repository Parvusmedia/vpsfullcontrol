#!/usr/bin/env bash
# Point ngaged.pmediaplus.com to Parvus (87.106.194.137) via Plesk DNS on nextconvers-vps.
# Run from a machine with SSH to parvus-vps (jump) and nextconvers-vps configured in ~/.ssh/config there.
set -euo pipefail

PARVUS="${PARVUS:-parvus-vps}"
OLD_IP="${OLD_IP:-82.223.3.205}"
NEW_IP="${NEW_IP:-87.106.194.137}"
SUB="${SUB:-ngaged}"
DOMAIN="pmediaplus.com"

ssh "$PARVUS" "ssh nextconvers-vps \"
  set -e
  plesk bin dns --del ${DOMAIN} -a ${SUB} -ip ${OLD_IP} 2>/dev/null || true
  plesk bin dns --add ${DOMAIN} -a ${SUB} -ip ${NEW_IP}
  plesk bin dns --info ${DOMAIN} | grep ${SUB}
\""

echo "DNS updated. After propagation, on parvus-vps:"
echo "  sudo certbot --nginx -d ${SUB}.${DOMAIN}"
