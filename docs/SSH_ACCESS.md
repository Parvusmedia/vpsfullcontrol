# Acceso SSH operativo al VPS

## Modelo

| Ítem | Valor |
|------|--------|
| Host | `87.106.194.137` |
| Puerto | **2222** (recomendado) o `22` |
| Usuario | **`cursorbot`** |
| Auth | contraseña **o** clave SSH |
| Root por SSH | deshabilitado (usar `sudo` / `sudo -i`) |

`cursorbot` tiene sudo NOPASSWD para operar `/opt/apps` y servicios.

## PuTTY (simple, con contraseña)

1. Host: `87.106.194.137`
2. Port: `2222`
3. Connection type: SSH
4. Connection → Data → Auto-login username: `cursorbot`
5. Open → introducir la contraseña de `cursorbot`

Si falla el puerto 22 desde tu red, usa siempre **2222** (debe estar permitido en el firewall IONOS).

## OpenSSH / PowerShell

```powershell
ssh -p 2222 cursorbot@87.106.194.137
```

Con clave (opcional):

```powershell
ssh -i $env:USERPROFILE\.ssh\id_ed25519 -p 2222 cursorbot@87.106.194.137
```

## Cloud agents / automatización

- Clave pública del agente Cursor: `cursor-agent-vps` en `~cursorbot/.ssh/authorized_keys`
- Runner self-hosted `ops` para workflows (`vps-ops`, `ssl-friendinme-app`, `vps-ssh-access`)

## Registrar otra clave pública

Actions → **vps-register-pubkey** → Run workflow (pegar línea `ssh-ed25519 AAAA...`).

## Reparar SSH

Actions → **vps-ssh-access** → Run workflow  
(ejecuta `/usr/local/sbin/parvus-ssh-setup`).

## FriendInMe (notas operativas)

- API: `127.0.0.1:8000` (`friendinme-api`)
- Web: `127.0.0.1:3010` (`friendinme-web`)
- Dominio canónico: `https://friendinme.app`
- Legacy `friendinme.pmediaplus.com` → 301 a `friendinme.app`
- **No** reutilizar el puerto 8000 para otros servicios (`ai-agent` legacy usa **8010**; `ai-agent-v3` usa **8004**)
