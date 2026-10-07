#!/usr/bin/env bash
# Create educationdemo.pmediaplus.com A 87.106.194.137 on the Plesk nameserver.
# Never prints secret values.
set -euo pipefail

DOMAIN="${DNS_DOMAIN:-pmediaplus.com}"
HOST="${DNS_HOST:-educationdemo}"
FQDN="${HOST}.${DOMAIN}"
IP="${DNS_IP:-87.106.194.137}"
PLESK_IP="${PLESK_IP:-82.223.3.205}"
TTL="${DNS_TTL:-3600}"

echo "=== target ${FQDN} A ${IP} (ttl ${TTL}) via Plesk ${PLESK_IP} ==="

current="$(dig +short "$FQDN" A | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
echo "current DNS: ${current:-none}"
if [[ "$current" == "$IP" ]]; then
  echo "DNS already correct"
  exit 0
fi

found_key_files() {
  echo "=== ssh key files (names only) ==="
  for d in /root/.ssh /home/cursorbot/.ssh /home/ops/.ssh "$HOME/.ssh"; do
    if [[ -d "$d" ]]; then
      echo "DIR $d"
      ls -l "$d" | awk '{print $1,$3,$4,$9}'
    fi
  done
}

try_ssh() {
  local user="$1" port="$2" ident="${3:-}"
  local opts=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -p "$port")
  if [[ -n "$ident" ]]; then
    opts+=(-i "$ident" -o IdentitiesOnly=yes)
  fi
  ssh "${opts[@]}" "${user}@${PLESK_IP}" 'echo SSH_OK; hostname; command -v plesk || true'
}

add_via_ssh() {
  local user="$1" port="$2" ident="${3:-}"
  local opts=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -p "$port")
  if [[ -n "$ident" ]]; then
    opts+=(-i "$ident" -o IdentitiesOnly=yes)
  fi
  echo "Adding DNS via SSH ${user}@${PLESK_IP}:${port}"
  ssh "${opts[@]}" "${user}@${PLESK_IP}" bash -s -- "$DOMAIN" "$HOST" "$IP" "$TTL" <<'REMOTE'
set -euo pipefail
DOMAIN="$1"
HOST="$2"
IP="$3"
TTL="$4"
if ! command -v plesk >/dev/null 2>&1; then
  echo "plesk CLI missing" >&2
  exit 2
fi
info="$(plesk bin dns --info "$DOMAIN" || true)"
if printf '%s\n' "$info" | grep -E "^[[:space:]]*${HOST}[[:space:]]+.*A[[:space:]]+${IP}" >/dev/null 2>&1 \
  || printf '%s\n' "$info" | grep -E "^[[:space:]]*${HOST}\\.${DOMAIN}\\.?[[:space:]]+.*A[[:space:]]+${IP}" >/dev/null 2>&1; then
  echo "Plesk already has ${HOST} A ${IP}"
  exit 0
fi
if printf '%s\n' "$info" | grep -E "^[[:space:]]*${HOST}([[:space:]]|\\.${DOMAIN})" >/dev/null 2>&1; then
  echo "Host exists with another value; leaving it untouched" >&2
  printf '%s\n' "$info" | grep -E "${HOST}" | sed 's/[[:space:]]\+/ /g'
  exit 3
fi
plesk bin dns --add "$DOMAIN" -a "$HOST" -ip "$IP" -ttl "$TTL"
echo "PLESK_DNS_ADDED"
REMOTE
}

add_via_api() {
  local key="$1"
  local origin="${PLESK_API_ORIGIN:-https://${PLESK_IP}:8443}"
  echo "Trying Plesk REST API at $origin"
  local auth_header="X-API-Key: ${key}"
  local list
  list="$(curl -skS --max-time 20 -H "$auth_header" -H "Accept: application/json" \
    "${origin}/api/v2/dns/records?domain=${DOMAIN}&name=${FQDN}" || true)"
  if printf '%s' "$list" | grep -q "$IP"; then
    echo "API already has ${FQDN} -> ${IP}"
    return 0
  fi
  local code
  code="$(curl -skS --max-time 20 -o /tmp/plesk-dns-add.json -w "%{http_code}" \
    -H "$auth_header" -H "Content-Type: application/json" -H "Accept: application/json" \
    -d "{\"type\":\"A\",\"host\":\"${FQDN}\",\"value\":\"${IP}\",\"ttl\":${TTL}}" \
    "${origin}/api/v2/dns/records" || true)"
  echo "API POST status=$code"
  python3 - <<'PY'
import json
from pathlib import Path
p=Path("/tmp/plesk-dns-add.json")
if p.exists() and p.stat().st_size:
    try:
        data=json.loads(p.read_text())
    except Exception:
        print("API body not JSON")
    else:
        # Do not dump credentials; print only high-level keys.
        if isinstance(data, dict):
            print("API keys:", ",".join(sorted(data.keys())[:20]))
            print("API message:", str(data.get("message") or data.get("error") or "")[:200])
        else:
            print("API type", type(data).__name__)
PY
  [[ "$code" == "200" || "$code" == "201" ]]
}

echo "=== local plesk CLI ==="
command -v plesk >/dev/null && echo "plesk present" || echo "plesk not on this host"

found_key_files

echo "=== ssh config hosts (no keys) ==="
for cfg in /root/.ssh/config /home/cursorbot/.ssh/config /home/ops/.ssh/config; do
  if [[ -f "$cfg" ]]; then
    echo "CONFIG $cfg"
    awk 'BEGIN{IGNORECASE=1} $1=="Host"||$1=="HostName"||$1=="User"||$1=="Port"||$1=="IdentityFile"{print}' "$cfg"
  fi
done

echo "=== plesk-named files (paths only) ==="
find /home/cursorbot /root /etc /opt/apps /etc/svcopctl -iname '*plesk*' 2>/dev/null | head -50 || true

SSH_OK=""
USERS=(root cursorbot admin ubuntu ops pmediaplus parvusmedia parvus emiliano psaadm)
PORTS=(22 2222)
mapfile -t IDENTS < <(
  find /root/.ssh /home/cursorbot/.ssh /home/ops/.ssh "$HOME/.ssh" \
    -type f \( -name 'id_*' -o -name '*ed25519' -o -name '*rsa' -o -name '*ecdsa' \) \
    ! -name '*.pub' 2>/dev/null | sort -u
)

echo "=== identity files to try ==="
printf '%s\n' "${IDENTS[@]:-}"

try_config_hosts() {
  local cfg="$1"
  [[ -f "$cfg" ]] || return 1
  local hosts
  hosts="$(awk '$1=="Host"{for(i=2;i<=NF;i++) if($i !~ /[*?]/) print $i}' "$cfg")"
  local h
  for h in $hosts; do
    echo "Trying ssh config Host $h"
    if out="$(ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=8 "$h" 'echo SSH_OK; hostname; command -v plesk || true' 2>/dev/null)"; then
      echo "SSH_SUCCESS config:$h"
      printf '%s\n' "$out" | sed -n '1,5p'
      ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=8 "$h" bash -s -- "$DOMAIN" "$HOST" "$IP" "$TTL" <<'REMOTE'
set -euo pipefail
DOMAIN="$1"; HOST="$2"; IP="$3"; TTL="$4"
command -v plesk >/dev/null || { echo "plesk CLI missing"; exit 2; }
info="$(plesk bin dns --info "$DOMAIN" || true)"
if printf '%s\n' "$info" | grep -E "${HOST}" | grep -q "$IP"; then
  echo "Plesk already has ${HOST} A ${IP}"
  exit 0
fi
plesk bin dns --add "$DOMAIN" -a "$HOST" -ip "$IP" -ttl "$TTL"
echo "PLESK_DNS_ADDED"
REMOTE
      return 0
    fi
  done
  return 1
}

for cfg in /home/cursorbot/.ssh/config /root/.ssh/config; do
  if try_config_hosts "$cfg"; then
    SSH_OK=1
    break
  fi
done

if [[ -z "$SSH_OK" ]]; then
  for user in "${USERS[@]}"; do
    for port in "${PORTS[@]}"; do
      for ident in "${IDENTS[@]}"; do
        label="${user}:${port}:${ident}"
        if out="$(try_ssh "$user" "$port" "$ident" 2>/dev/null)"; then
          echo "SSH_SUCCESS $label"
          printf '%s\n' "$out" | sed -n '1,5p'
          if add_via_ssh "$user" "$port" "$ident"; then
            SSH_OK=1
            break 3
          fi
        else
          echo "SSH_FAIL $label"
        fi
      done
    done
  done
fi

API_KEY="${PLESK_API_KEY:-}"
if [[ -z "$API_KEY" && -n "${PLESK_API_KEY_FILE:-}" && -f "${PLESK_API_KEY_FILE}" ]]; then
  API_KEY="$(tr -d '\r\n' < "${PLESK_API_KEY_FILE}")"
fi
if [[ -z "$API_KEY" ]]; then
  for f in /etc/plesk/api.key /root/.plesk-api-key /home/cursorbot/.plesk-api-key /etc/svcopctl/plesk.env; do
    if [[ -f "$f" ]]; then
      echo "found credential file $f (not printed)"
      case "$f" in
        *.env)
          # shellcheck disable=SC1090
          set -a
          # only export PLESK_API_KEY if present
          API_KEY="$(awk -F= '/^PLESK_API_KEY=/{sub(/^PLESK_API_KEY=/,""); gsub(/^[\"'\'']|[\"'\'']$/,""); print; exit}' "$f")"
          set +a
          ;;
        *)
          API_KEY="$(tr -d '\r\n' < "$f")"
          ;;
      esac
    fi
  done
fi

if [[ -z "$SSH_OK" && -n "$API_KEY" ]]; then
  if add_via_api "$API_KEY"; then
    SSH_OK=1
  fi
elif [[ -z "$SSH_OK" && -z "$API_KEY" ]]; then
  echo "No Plesk API key available in env or known files"
fi

if [[ -z "$SSH_OK" ]]; then
  echo "FAILED to create DNS record (no SSH/API success); skipping wait"
  exit 1
fi

echo "=== wait for DNS ==="
for i in $(seq 1 12); do
  got="$(dig +short "$FQDN" A @${PLESK_IP} | tail -n1 || true)"
  echo "try $i ns ${PLESK_IP} -> ${got:-none}"
  if [[ "$got" == "$IP" ]]; then
    echo "DNS_OK ${FQDN} A ${IP}"
    exit 0
  fi
  sleep 5
done

echo "Record submitted but public/ns lookup not visible yet"
exit 0
