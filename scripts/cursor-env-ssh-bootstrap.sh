#!/usr/bin/env bash
# Bootstrap SSH access from a Cursor Cloud / local agent environment to Parvus VPS.
# Expects private key in env var CURSOR_VPS_SSH_PRIVATE_KEY (PEM/OpenSSH private key body).
set -euo pipefail

HOST="${CURSOR_VPS_HOST:-87.106.194.137}"
PORT="${CURSOR_VPS_PORT:-2222}"
USER="${CURSOR_VPS_USER:-cursorbot}"
KEY_PATH="${CURSOR_VPS_KEY_PATH:-$HOME/.ssh/cursor_vps_access}"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [[ -n "${CURSOR_VPS_SSH_PRIVATE_KEY:-}" ]]; then
  printf '%s\n' "$CURSOR_VPS_SSH_PRIVATE_KEY" > "$KEY_PATH"
  chmod 600 "$KEY_PATH"
elif [[ ! -f "$KEY_PATH" ]]; then
  echo "Missing CURSOR_VPS_SSH_PRIVATE_KEY and no key at $KEY_PATH" >&2
  exit 1
fi

cat > "$HOME/.ssh/config" <<CFG
Host parvus-vps
  HostName ${HOST}
  Port ${PORT}
  User ${USER}
  IdentityFile ${KEY_PATH}
  IdentitiesOnly yes
  ServerAliveInterval 30
  StrictHostKeyChecking accept-new
CFG
chmod 600 "$HOME/.ssh/config"

echo "SSH ready: ssh parvus-vps"
ssh -o BatchMode=yes -o ConnectTimeout=10 parvus-vps 'echo OK; hostname; whoami'
