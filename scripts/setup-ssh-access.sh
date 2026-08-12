#!/usr/bin/env bash
set -euo pipefail

AGENT_PUB='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKgn07nToDRuZWb4fq2DL9ImtRQJmk1ewNMFW8WcfXjH cursor-agent-vps'
ALT_PORT=2222

echo "=== preflight ==="
hostname; date -u
sshd -T 2>/dev/null | egrep '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication|authorizedkeysfile|allowusers|denyusers) ' || true

install_keys_for() {
  local home="$1"
  local user="$2"
  mkdir -p "$home/.ssh"
  touch "$home/.ssh/authorized_keys"
  if ! grep -qxF "$AGENT_PUB" "$home/.ssh/authorized_keys" 2>/dev/null; then
    printf '%s\n' "$AGENT_PUB" >> "$home/.ssh/authorized_keys"
  fi
  # Deduplicate exact lines
  awk 'NF && !seen[$0]++' "$home/.ssh/authorized_keys" > "$home/.ssh/authorized_keys.tmp"
  mv "$home/.ssh/authorized_keys.tmp" "$home/.ssh/authorized_keys"
  chown -R "$user:$user" "$home/.ssh"
  chmod 700 "$home/.ssh"
  chmod 600 "$home/.ssh/authorized_keys"
  echo "keys for $user:"
  ssh-keygen -lf "$home/.ssh/authorized_keys" || true
}

echo "=== install keys ==="
install_keys_for /root root
if id cursorbot >/dev/null 2>&1; then
  install_keys_for "$(getent passwd cursorbot | cut -d: -f6)" cursorbot
fi
if id ubuntu >/dev/null 2>&1; then
  install_keys_for "$(getent passwd ubuntu | cut -d: -f6)" ubuntu
fi

echo "=== collect known public keys on disk (for ops visibility) ==="
find /home /root -path '*/.ssh/*.pub' 2>/dev/null | head -50 || true

echo "=== sshd drop-in ==="
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/50-parvus-access.conf <<CFG
# Parvus Media operational SSH access
Port 22
Port ${ALT_PORT}
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
CFG

rm -f /etc/ssh/sshd_config.d/99-root-login.conf

# Normalize main file overrides (first value wins depending on Include order;
# Ubuntu puts Include at top, but some images set PermitRootLogin later).
if grep -qE '^PermitRootLogin ' /etc/ssh/sshd_config; then
  sed -i 's/^PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
fi
if grep -qE '^PasswordAuthentication ' /etc/ssh/sshd_config; then
  sed -i 's/^PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
fi
# Ensure Include is present
if ! grep -qE '^Include /etc/ssh/sshd_config.d/\*\.conf' /etc/ssh/sshd_config; then
  sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config
fi

echo "=== host firewall ==="
if command -v ufw >/dev/null 2>&1; then
  ufw allow 22/tcp || true
  ufw allow ${ALT_PORT}/tcp || true
  ufw status || true
fi
# iptables fallback accept (idempotent-ish)
if command -v iptables >/dev/null 2>&1; then
  iptables -C INPUT -p tcp --dport 22 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 22 -j ACCEPT || true
  iptables -C INPUT -p tcp --dport ${ALT_PORT} -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport ${ALT_PORT} -j ACCEPT || true
fi

echo "=== validate & restart ssh ==="
sshd -t
systemctl restart ssh || systemctl restart sshd
sleep 2
echo "effective:"
sshd -T | egrep '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication) ' || true
echo "listeners:"
ss -tlnp | egrep ':22|:2222' || true

echo "=== auth log tail ==="
journalctl -u ssh -u sshd --no-pager -n 50 || true

echo "SETUP_OK port22+${ALT_PORT} key-only root/cursorbot/ubuntu"
