# Cursor ↔ VPS SSH (local y cloud)

Objetivo: que **cualquier agente Cursor** (IDE local o Cloud Agent) pueda entrar al VPS Parvus y operar los proyectos en `/opt/apps`.

## Datos del VPS

| Campo | Valor |
|-------|--------|
| Host | `87.106.194.137` |
| Puerto | `2222` (preferido) / `22` |
| Usuario | `cursorbot` |
| Clave dedicada Cursor | `cursor_vps_access` (ed25519) |
| Alias SSH | `parvus-vps` |

Proyectos en el VPS: `/opt/apps/*` (friendinme, linkedinreport, fly456bot, prospeccion-*, etc.).

## 1) Cursor local (Windows / macOS / Linux)

### A. Guardar la clave privada

Copia el archivo privado `cursor_vps_access` a:

- Windows: `C:\Users\<tu>\.ssh\cursor_vps_access`
- macOS/Linux: `~/.ssh/cursor_vps_access`

Permisos (macOS/Linux):

```bash
chmod 600 ~/.ssh/cursor_vps_access
```

### B. SSH config

Añade a `~/.ssh/config` (Windows: `C:\Users\<tu>\.ssh\config`):

```
Host parvus-vps
  HostName 87.106.194.137
  Port 2222
  User cursorbot
  IdentityFile ~/.ssh/cursor_vps_access
  IdentitiesOnly yes
  ServerAliveInterval 30
```

### C. Probar

```bash
ssh parvus-vps
```

En Cursor Agent (local), ya puede ejecutar:

```bash
ssh parvus-vps 'ls /opt/apps'
ssh parvus-vps 'sudo systemctl status friendinme-api --no-pager'
```

También puedes usar **Remote-SSH** al host `parvus-vps`.

> Alternativa sin la clave dedicada: tu clave `id_ed25519` (`cursorbot-vps`) ya está autorizada, o password de `cursorbot` por PuTTY.

## 2) Cursor Cloud Agents

Los pods de Cloud Agent **no** heredan tu `~/.ssh` local.

### Opción automática (sin secrets en el dashboard)

Los checkouts de Cloud Agent suelen estar desactualizados. En el otro entorno pega **esto** (coge el script de `main`, no el local):

```bash
curl -fsSL https://raw.githubusercontent.com/Parvusmedia/vpsfullcontrol/main/scripts/cursor-env-ssh-bootstrap.sh | bash
```

Eso descarga la clave del drop privado o, si `gh` no puede leerlo, publica una pubkey y el VPS la ingiere. No hace falta el secret `CURSOR_VPS_SSH_PRIVATE_KEY`.

### Opción secret (opcional)

Si existe el secret de entorno `CURSOR_VPS_SSH_PRIVATE_KEY`, el bootstrap lo usa primero y no toca el drop repo.

### Opción por repo

Añade en `.cursor/environment.json`:

```json
{
  "install": "bash scripts/cursor-env-ssh-bootstrap.sh || true"
}
```

(el install ya está en este repo; el bootstrap coge la clave del drop privado o del secret si existe).

### Sin secret (fallback)

Usa GitHub Actions self-hosted (`vps-ops`, `ssl-friendinme-app`) que ya corren **dentro** del VPS.

## 3) Qué puede hacer el agente en el VPS

```bash
ssh parvus-vps 'ls /opt/apps'
ssh parvus-vps 'sudo systemctl status friendinme-api friendinme-web --no-pager'
ssh parvus-vps 'cd /opt/apps/friendinme && git status'
```

`cursorbot` tiene sudo. No uses `root` por SSH.

## 4) Rotar / reparar acceso

- Reinstalar claves del agente: Actions → `vps-ssh-access`
- Añadir otra pubkey de workstation: Actions → `vps-register-pubkey`
- Doc general PuTTY/password: `docs/SSH_ACCESS.md`

## 5) Varios VPS (futuro)

Si añades más máquinas, repite el mismo `authorized_keys` en `cursorbot` y añade hosts al SSH config:

```
Host parvus-vps-2
  HostName x.x.x.x
  Port 2222
  User cursorbot
  IdentityFile ~/.ssh/cursor_vps_access
```
