#!/usr/bin/env bash
# Bootstrap SSH from a Cursor Cloud / local agent to the Parvus Ionos VPS.
# Priority:
#   1) CURSOR_VPS_SSH_PRIVATE_KEY env (Cursor environment secret)
#   2) existing key file at CURSOR_VPS_KEY_PATH
#   3) private drop repo Parvusmedia/vps-cursor-ssh (fetched with gh)
set -euo pipefail

HOST="${CURSOR_VPS_HOST:-87.106.194.137}"
PORT="${CURSOR_VPS_PORT:-2222}"
USER="${CURSOR_VPS_USER:-cursorbot}"
KEY_PATH="${CURSOR_VPS_KEY_PATH:-$HOME/.ssh/cursor_vps_access}"
DROP_REPO="${CURSOR_VPS_DROP_REPO:-Parvusmedia/vps-cursor-ssh}"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

fetch_drop_file() {
  local relpath="$1"
  local dest="$2"
  gh api "repos/${DROP_REPO}/contents/${relpath}" --jq .content | tr -d '\n' | base64 -d > "$dest"
}

install_key_from_drop_repo() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh not available; cannot fetch ${DROP_REPO}" >&2
    return 1
  fi
  # A repo-scoped GITHUB_TOKEN cannot read the private drop repo.
  if [[ -n "${GITHUB_TOKEN:-}" ]] && ! gh api "repos/${DROP_REPO}/contents/cursor_vps_access.pub" --jq .sha >/dev/null 2>&1; then
    unset GITHUB_TOKEN
  fi
  if ! gh auth status >/dev/null 2>&1 && [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
    echo "gh is not authenticated; cannot fetch ${DROP_REPO}" >&2
    return 1
  fi
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  chmod 700 "$tmp"
  fetch_drop_file cursor_vps_access.enc "$tmp/cursor_vps_access.enc"
  fetch_drop_file unwrap.pass "$tmp/unwrap.pass"
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
    -in "$tmp/cursor_vps_access.enc" \
    -out "$KEY_PATH" \
    -pass file:"$tmp/unwrap.pass"
  chmod 600 "$KEY_PATH"
}

if [[ -n "${CURSOR_VPS_SSH_PRIVATE_KEY:-}" ]]; then
  printf '%s\n' "$CURSOR_VPS_SSH_PRIVATE_KEY" > "$KEY_PATH"
  chmod 600 "$KEY_PATH"
elif [[ -f "$KEY_PATH" ]]; then
  chmod 600 "$KEY_PATH"
else
  install_key_from_drop_repo
fi

if [[ ! -s "$KEY_PATH" ]]; then
  echo "Missing SSH key at $KEY_PATH (env, local file, and ${DROP_REPO} all failed)" >&2
  exit 1
fi

SSH_CFG="$HOME/.ssh/config"
if [[ ! -f "$SSH_CFG" ]] || ! grep -qE '^Host[[:space:]]+parvus-vps$' "$SSH_CFG" 2>/dev/null; then
  cat >> "$SSH_CFG" <<CFG

Host parvus-vps
  HostName ${HOST}
  Port ${PORT}
  User ${USER}
  IdentityFile ${KEY_PATH}
  IdentitiesOnly yes
  ServerAliveInterval 30
  StrictHostKeyChecking accept-new

Host parvus-vps-22
  HostName ${HOST}
  Port 22
  User ${USER}
  IdentityFile ${KEY_PATH}
  IdentitiesOnly yes
  ServerAliveInterval 30
  StrictHostKeyChecking accept-new
CFG
fi
chmod 600 "$SSH_CFG"

echo "SSH ready: ssh parvus-vps"
if ssh -F "$SSH_CFG" -o BatchMode=yes -o ConnectTimeout=10 parvus-vps 'echo OK; hostname; whoami'; then
  exit 0
fi
echo "Port ${PORT} failed, trying 22..." >&2
ssh -F "$SSH_CFG" -o BatchMode=yes -o ConnectTimeout=10 parvus-vps-22 'echo OK; hostname; whoami'
