#!/usr/bin/env bash
# Merge all cloud agent pubkeys from cloud-keys/*.pub into cursorbot authorized_keys.
# Run on the VPS (self-hosted runner or manually after cloning cursor-cloud-ssh-keys).
set -euo pipefail

KEYS_DIR="${1:-${GITHUB_WORKSPACE:-}/cloud-keys}"
if [[ ! -d "$KEYS_DIR" ]]; then
  echo "Keys directory not found: $KEYS_DIR" >&2
  exit 1
fi

CB_HOME="$(getent passwd cursorbot | cut -d: -f6)"
AUTH="$CB_HOME/.ssh/authorized_keys"
TMP="$(mktemp)"

if [[ -f "$AUTH" ]]; then
  sudo cat "$AUTH" > "$TMP"
else
  : > "$TMP"
fi

added=0
for pub in "$KEYS_DIR"/*.pub; do
  [[ -f "$pub" ]] || continue
  line="$(tr -d '\r' < "$pub" | head -n1)"
  case "$line" in
    ssh-ed25519\ *|ssh-rsa\ *|ecdsa-sha2-nistp256\ *) ;;
    *) continue ;;
  esac
  if ! grep -qxF "$line" "$TMP"; then
    printf '%s\n' "$line" >> "$TMP"
    added=$((added + 1))
  fi
done

sudo mkdir -p "$CB_HOME/.ssh"
sudo install -m 600 -o cursorbot -g cursorbot "$TMP" "$AUTH"
sudo chmod 700 "$CB_HOME/.ssh"
rm -f "$TMP"

echo "Synced cloud SSH keys from $KEYS_DIR (added $added new entries)."
ssh-keygen -lf <(sudo cat "$AUTH") || sudo wc -l "$AUTH"
