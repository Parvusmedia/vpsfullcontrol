# Acceso SSH operativo al VPS

## Modelo

- Usuario SSH: **`cursorbot`** (único permitido vía `AllowUsers`)
- Auth: **solo clave pública** (sin password)
- Puertos: **22** y **2222**
- Root SSH: deshabilitado a propósito
- `cursorbot` tiene sudo NOPASSWD para operar proyectos en `/opt/apps`

## PuTTY / Windows

1. En IONOS Cloud Panel → Firewall del VPS → **Permitir TCP 2222** (todas las IPs).  
   El 22 ya está abierto; si tu ISP bloquea salida al 22, usa **2222**.
2. En PowerShell, copia tu clave pública:

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

3. Regístrala en el VPS (Actions → **vps-register-pubkey** → Run workflow pegando la línea `ssh-ed25519 ...`),  
   o pásasela al agente Cursor para que la instale.
4. PuTTY:
   - Host: `87.106.194.137`
   - Port: `2222` (o `22` si tu red no lo bloquea)
   - Connection → SSH → Auth → Private key: `C:\Users\<tu>\.ssh\id_ed25519`  
     (si PuTTY pide `.ppk`, convierte con PuTTYgen: Conversions → Import key)
   - Usuario: `cursorbot`

## Cloud agents / automatización

- Clave pública del agente: `cursor-agent-vps` (instalada en `~cursorbot/.ssh/authorized_keys`)
- Runner self-hosted `ops` sigue siendo el canal de operaciones vía GitHub Actions (`vps-ops`, `ssl-friendinme-app`, `vps-ssh-access`)

## Reparar acceso

```text
Actions → vps-ssh-access → Run workflow
```

Ejecuta `/usr/local/sbin/parvus-ssh-setup` en el VPS.
