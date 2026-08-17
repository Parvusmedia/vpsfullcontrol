#!/usr/bin/env bash
# Read-only inventory of the VPS before touching live-fare-demo.
set -euo pipefail
echo "=== host ==="
hostname; date -u; whoami
echo "=== /opt/apps ==="
ls -la /opt/apps 2>/dev/null || echo "NO /opt/apps"
echo "=== docker ==="
if command -v docker >/dev/null 2>&1; then
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
  docker network ls || true
else
  echo "docker not installed"
fi
echo "=== listeners ==="
ss -tlnp | sed -n '1,80p' || netstat -tlnp | sed -n '1,80p' || true
echo "=== nginx sites ==="
ls -la /etc/nginx/sites-enabled /etc/nginx/sites-available 2>/dev/null || true
echo "=== nginx server_name ==="
grep -R "server_name" /etc/nginx/sites-enabled /etc/nginx/sites-available 2>/dev/null | sed -n '1,80p' || true
echo "=== dns flights.pmediaplus.com ==="
getent hosts flights.pmediaplus.com || true
dig +short flights.pmediaplus.com A || true
echo "=== timers ==="
systemctl list-timers --all | sed -n '1,40p' || true
echo "INSPECT_OK"
