#!/usr/bin/env bash
set -euo pipefail

AGENT_PUB='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKgn07nToDRuZWb4fq2DL9ImtRQJmk1ewNMFW8WcfXjH cursor-agent-vps'
ALT_PORT=2222

echo "=== preflight ==="
hostname; date -u
id
sshd -T 2>/dev/null | egrep '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication|authorizedkeysfile|allowusers|denyusers|listenaddress) ' || true

install_keys_for() {
  local home="$1"
  local user="$2"
  mkdir -p "$home/.ssh"
  touch "$home/.ssh/authorized_keys"

  # Preserve existing keys; ensure agent key present
  if ! grep -qxF "$AGENT_PUB" "$home/.ssh/authorized_keys" 2>/dev/null; then
    printf '%s\n' "$AGENT_PUB" >> "$home/.ssh/authorized_keys"
  fi

  # Also include any existing keys from common deploy users (dedupe later)
  chown -R "$user:$user" "$home/.ssh"
  chmod 700 "$home/.ssh"
  chmod 600 "$home/.ssh/authorized_keys"
  echo "keys for $user:" 
  awk '{print $1,$NF}' "$home/.ssh/authorized_keys" || true
}

echo "=== install keys ==="
install_keys_for /root root
if id cursorbot >/dev/null 2>&1; then
  install_keys_for /home/cursorbot cursorbot
fi
if id ubuntu >/dev/null 2>&1; then
  install_keys_for /home/ubuntu ubuntu
fi
if id ops >/dev/null 2>&1; then
  # ops home may vary
  OPS_HOME=$(getent passwd ops | cut -d: -f6)
  install_keys_for "$OPS_HOME" ops
fi

echo "=== sshd drop-in (operational) ==="
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/50-parvus-access.conf <<EOF
# Parvus Media operational SSH access
Port 22
Port ${ALT_PORT}
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
EOF

# Remove conflicting previous drop-in that enabled passwords
rm -f /etc/ssh/sshd_config.d/99-root-login.conf

# If main sshd_config hard-sets PermitRootLogin after Include, force-comment known blockers
if grep -qE '^PermitRootLogin ' /etc/ssh/sshd_config; then
  sed -i 's/^PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
fi
if grep -qE '^PasswordAuthentication ' /etc/ssh/sshd_config; then
  sed -i 's/^PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
fi

echo "=== firewall (host) ==="
if command -v ufw >/dev/null 2>&1; then
  ufw status || true
  ufw allow 22/tcp || true
  ufw allow ${ALT_PORT}/tcp || true
fi

echo "=== validate & restart ssh ==="
sshd -t
systemctl restart ssh || systemctl restart sshd
sleep 2
sshd -T | egrep '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication) ' || true
ss -tlnp | egrep ':22|:2222' || true

echo "=== recent auth failures ==="
journalctl -u ssh -u sshd --no-pager -n 40 || true

echo "=== authorized_keys fingerprints ==="
for f in /root/.ssh/authorized_keys /home/cursorbot/.ssh/authorized_keys /home/ubuntu/.ssh/authorized_keys; do
  if [ -f "$f" ]; then
    echo "-- $f"
    ssh-keygen -lf "$f" || cat "$f"
  fi
done

echo "SETUP_OK"
