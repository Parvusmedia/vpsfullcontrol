#!/usr/bin/env bash
# Read-only inventory before touching education-ai-advisor.
set -euo pipefail
echo "=== host ==="
hostname; date -u; whoami
echo "=== /opt/apps ==="
ls -la /opt/apps 2>/dev/null || echo "NO /opt/apps"
echo "=== existing usj vhosts ==="
grep -R "server_name" /etc/nginx/sites-enabled /etc/nginx/sites-available 2>/dev/null | grep -i usj || true
echo "=== listeners 8021 ==="
ss -tlnp | grep -E ':8021|:8000|:8004|:8005|:8010' || true
echo "=== dns ==="
dig +short usj.pmediaplus.com A || true
dig +short educationdemo.pmediaplus.com A || true
dig +short educationdemo.pmediaplus.com A @82.223.3.205 || true
echo "=== systemd ==="
systemctl is-active education-ai-advisor.service 2>/dev/null || true
echo "INSPECT_OK"
