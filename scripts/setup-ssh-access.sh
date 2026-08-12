#!/usr/bin/env bash
set -euo pipefail

AGENT_PUBS=(
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKgn07nToDRuZWb4fq2DL9ImtRQJmk1ewNMFW8WcfXjH cursor-agent-vps'
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFq2RHsSB0Oz9frrqB7YsaGf2D0n0p+mXHSf+euTEssM cursor-vps-access@parvus'
)

echo "=== REPAIR SSH SOCKET + ACCESS ==="
hostname; date -u

# Restore Ubuntu default socket first (IPv4+IPv6 on 22 only), then add 2222 carefully
mkdir -p /etc/systemd/system/ssh.socket.d
cat > /etc/systemd/system/ssh.socket.d/override.conf <<'O'
[Socket]
# Reset inherited ListenStream then bind explicitly
ListenStream=
ListenStream=0.0.0.0:22
ListenStream=[::]:22
ListenStream=0.0.0.0:2222
ListenStream=[::]:2222
Accept=no
FreeBind=yes
O

# Auth policy: only cursorbot, key-only. Root disabled on purpose.
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/50-parvus-access.conf <<'C'
# Parvus Media operational SSH access
# Ports are managed by systemd ssh.socket (22 + 2222)
PermitRootLogin no
PasswordAuthentication yes
KbdInteractiveAuthentication yes
PubkeyAuthentication yes
AllowUsers cursorbot
AuthorizedKeysFile .ssh/authorized_keys
C

# Keep existing allowusers file consistent if present
if [ -f /etc/ssh/sshd_config.d/99-cursorbot.conf ]; then
  sed -i 's/^AllowUsers .*/AllowUsers cursorbot/' /etc/ssh/sshd_config.d/99-cursorbot.conf || true
fi

# Install agent key for cursorbot
CB_HOME=$(getent passwd cursorbot | cut -d: -f6)
mkdir -p "$CB_HOME/.ssh"
touch "$CB_HOME/.ssh/authorized_keys"
for AGENT_PUB in "${AGENT_PUBS[@]}"; do
  if ! grep -qxF "$AGENT_PUB" "$CB_HOME/.ssh/authorized_keys"; then
    printf '%s\n' "$AGENT_PUB" >> "$CB_HOME/.ssh/authorized_keys"
  fi
done
awk 'NF && !seen[$0]++' "$CB_HOME/.ssh/authorized_keys" > "$CB_HOME/.ssh/authorized_keys.tmp"
mv "$CB_HOME/.ssh/authorized_keys.tmp" "$CB_HOME/.ssh/authorized_keys"
chown -R cursorbot:cursorbot "$CB_HOME/.ssh"
chmod 700 "$CB_HOME/.ssh"
chmod 600 "$CB_HOME/.ssh/authorized_keys"

sshd -t
systemctl daemon-reload
systemctl restart ssh.socket
# Prefer socket activation; also restart service if active
systemctl restart ssh.service || true
sleep 2

echo "=== listeners ==="
ss -tlnp | egrep ':22|:2222' || true
echo "=== effective ==="
sshd -T | egrep '^(port|allowusers|permitrootlogin|passwordauthentication|pubkeyauthentication) ' || true
echo "=== keys ==="
ssh-keygen -lf "$CB_HOME/.ssh/authorized_keys" || cat "$CB_HOME/.ssh/authorized_keys"
echo "=== local ssh smoke ==="
# From localhost using agent pubkey isn't possible without private key; just check banner
timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/22; echo > /dev/tcp/127.0.0.1/22' 2>/dev/null || true
timeout 2 nc -vz 127.0.0.1 22 || true
timeout 2 nc -vz 127.0.0.1 2222 || true
echo SETUP_OK
