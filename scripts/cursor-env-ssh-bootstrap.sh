#!/usr/bin/env bash
# Bootstrap SSH from a Cursor Cloud / local agent to the Parvus Ionos VPS.
# Always prefer this copy from main (cloud checkouts are often stale):
#   curl -fsSL https://raw.githubusercontent.com/Parvusmedia/vpsfullcontrol/main/scripts/cursor-env-ssh-bootstrap.sh | bash
#
# Priority:
#   1) CURSOR_VPS_SSH_PRIVATE_KEY env
#   2) existing key file
#   3) private drop repo Parvusmedia/vps-cursor-ssh
#   4) generate a local key and publish the pubkey for the VPS to ingest
set -euo pipefail

HOST="${CURSOR_VPS_HOST:-87.106.194.137}"
PORT="${CURSOR_VPS_PORT:-2222}"
USER="${CURSOR_VPS_USER:-cursorbot}"
KEY_PATH="${CURSOR_VPS_KEY_PATH:-$HOME/.ssh/cursor_vps_access}"
DROP_REPO="${CURSOR_VPS_DROP_REPO:-Parvusmedia/vps-cursor-ssh}"
CTRL_REPO="${CURSOR_VPS_CTRL_REPO:-Parvusmedia/vpsfullcontrol}"
KEYS_BRANCH="${CURSOR_VPS_KEYS_BRANCH:-cursor-cloud-ssh-keys}"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

write_ssh_config() {
  local cfg="$HOME/.ssh/config"
  if [[ ! -f "$cfg" ]] || ! grep -qE '^Host[[:space:]]+parvus-vps$' "$cfg" 2>/dev/null; then
    cat >> "$cfg" <<CFG

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
  chmod 600 "$cfg"
}

ssh_ok() {
  local cfg="$HOME/.ssh/config"
  ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=8 parvus-vps 'echo OK; hostname; whoami' 2>/dev/null \
    || ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=8 parvus-vps-22 'echo OK; hostname; whoami' 2>/dev/null
}

fetch_drop_file() {
  local relpath="$1"
  local dest="$2"
  gh api "repos/${DROP_REPO}/contents/${relpath}" --jq .content | tr -d '\n' | base64 -d > "$dest"
}

install_key_from_drop_repo() {
  command -v gh >/dev/null 2>&1 || return 1
  if [[ -n "${GITHUB_TOKEN:-}" ]] && ! gh api "repos/${DROP_REPO}/contents/cursor_vps_access.pub" --jq .sha >/dev/null 2>&1; then
    unset GITHUB_TOKEN
  fi
  if ! gh auth status >/dev/null 2>&1 && [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
    return 1
  fi
  local tmp
  tmp="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap "rm -rf '$tmp'" RETURN
  chmod 700 "$tmp"
  fetch_drop_file cursor_vps_access.enc "$tmp/cursor_vps_access.enc"
  fetch_drop_file unwrap.pass "$tmp/unwrap.pass"
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
    -in "$tmp/cursor_vps_access.enc" \
    -out "$KEY_PATH" \
    -pass file:"$tmp/unwrap.pass"
  chmod 600 "$KEY_PATH"
}

publish_pubkey_for_vps() {
  command -v gh >/dev/null 2>&1 || return 1
  local pub content_b64 sha id path
  pub="$(cat "${KEY_PATH}.pub")"
  case "$pub" in
    ssh-ed25519\ *|ssh-rsa\ *|ecdsa-sha2-nistp256\ *) ;;
    *) echo "generated pubkey has unexpected format" >&2; return 1 ;;
  esac
  id="$(printf '%s-%s' "${HOSTNAME:-cloud}" "$(date +%s)" | tr -cd 'a-zA-Z0-9._-')"
  path="cloud-keys/${id}.pub"
  content_b64="$(printf '%s\n' "$pub" | base64 -w0 2>/dev/null || printf '%s\n' "$pub" | base64)"
  sha="$(gh api "repos/${CTRL_REPO}/contents/${path}?ref=${KEYS_BRANCH}" --jq .sha 2>/dev/null || true)"
  if [[ -n "$sha" ]]; then
    gh api --method PUT "repos/${CTRL_REPO}/contents/${path}" \
      -f message="register cloud agent pubkey ${id}" \
      -f content="$content_b64" \
      -f branch="$KEYS_BRANCH" \
      -f sha="$sha" >/dev/null
  else
    gh api --method PUT "repos/${CTRL_REPO}/contents/${path}" \
      -f message="register cloud agent pubkey ${id}" \
      -f content="$content_b64" \
      -f branch="$KEYS_BRANCH" >/dev/null
  fi
  echo "Published pubkey to ${CTRL_REPO}@${KEYS_BRANCH}:${path}"
  gh workflow run vps-sync-cloud-ssh-keys.yml -R "$CTRL_REPO" >/dev/null 2>&1 \
    || gh api "repos/${CTRL_REPO}/actions/workflows/vps-sync-cloud-ssh-keys.yml/dispatches" \
         -f ref=main >/dev/null 2>&1 \
    || true
  gh workflow run vps-register-pubkey.yml -R "$CTRL_REPO" -f pubkey="$pub" >/dev/null 2>&1 \
    || gh api "repos/${CTRL_REPO}/actions/workflows/vps-register-pubkey.yml/dispatches" \
         -f ref=main -f "inputs[pubkey]=${pub}" >/dev/null 2>&1 \
    || true
}

register_ephemeral_key() {
  if [[ ! -f "$KEY_PATH" ]]; then
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "cursor-cloud-$(hostname)-$(date +%s)" >/dev/null
    chmod 600 "$KEY_PATH" "${KEY_PATH}.pub"
  fi
  publish_pubkey_for_vps
}

if [[ -n "${CURSOR_VPS_SSH_PRIVATE_KEY:-}" ]]; then
  printf '%s\n' "$CURSOR_VPS_SSH_PRIVATE_KEY" > "$KEY_PATH"
  chmod 600 "$KEY_PATH"
elif [[ -f "$KEY_PATH" ]]; then
  chmod 600 "$KEY_PATH"
elif install_key_from_drop_repo; then
  echo "Loaded SSH key from ${DROP_REPO}"
else
  echo "Drop repo unavailable; registering an ephemeral cloud pubkey on the VPS..."
  register_ephemeral_key
fi

if [[ ! -s "$KEY_PATH" ]]; then
  echo "Could not install an SSH key for parvus-vps" >&2
  exit 1
fi

write_ssh_config

echo "SSH ready: ssh parvus-vps"
if ssh_ok; then
  exit 0
fi

echo "Waiting for VPS to ingest pubkey..."
for _ in $(seq 1 30); do
  sleep 4
  if ssh_ok; then
    exit 0
  fi
done

echo "SSH to ${USER}@${HOST} still failing after pubkey publish." >&2
echo "Fingerprint:" >&2
ssh-keygen -lf "${KEY_PATH}.pub" >&2 || true
exit 1
