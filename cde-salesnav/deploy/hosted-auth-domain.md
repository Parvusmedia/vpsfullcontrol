# White-label LinkedIn connect — `connect.companydataenrichment.com`

Opción 2: subdominio propio para el wizard de Unipile Hosted Auth (sin iframe).

## 1. DNS (registrar / Piensa Solutions)

El dominio usa nameservers públicos **Piensa Solutions** (`ns97.piensasolutions.com`, `ns98.piensasolutions.com`).  
El CNAME también está en **Plesk** del VPS (`82.223.3.205`). El backend solo reescribe la URL cuando **DNS + certificado SSL** de Unipile están listos; si no, usa `account.unipile.com`.

Crear un registro **CNAME** en el panel DNS de Piensa (Área de Cliente → dominio → DNS):

| Campo   | Valor                    |
|---------|--------------------------|
| Host    | `connect`                |
| Type    | `CNAME`                  |
| Target  | `account.unipile.com`    |

Verificar propagación:

```bash
dig +short connect.companydataenrichment.com CNAME @ns97.piensasolutions.com
# debe devolver: account.unipile.com.
```

### Estado DNS (2026-08-31)

| Check | Resultado |
|-------|-----------|
| CNAME público | `connect` → `account.unipile.com` ✅ |
| HTTPS / certificado | **Pendiente Unipile** — cert actual: `account-auth.allconnects.ai` → `NET::ERR_CERT_COMMON_NAME_INVALID` |

Hasta que Unipile habilite el dominio, el backend **no reescribe** la URL (Connect usa `account.unipile.com`).

## 2. Validación en Unipile (obligatorio para HTTPS)

1. Entrar al [Unipile Dashboard](https://dashboard.unipile.com) → **Hosted Auth**.
2. En **Hosted auth domain**, enviar `connect.companydataenrichment.com` (CNAME ya debe estar activo en Piensa).
3. Esperar a que aparezca en **Enabled domains** — Unipile genera el certificado Let's Encrypt para tu subdominio.
4. Verificar certificado:

```bash
curl -sSI https://connect.companydataenrichment.com/ | head -3
# Sin error SSL; el cert debe incluir connect.companydataenrichment.com
```

5. Si tarda >24h, contactar soporte Unipile con: `https://connect.companydataenrichment.com`

Requisito: cuenta Unipile con suscripción activa.

## 3. Configuración en el servidor

En `/var/www/vhosts/companydataenrichment.com/private/cde/unipile.env`:

```env
SALESNAV_HOSTED_AUTH_DOMAIN=connect.companydataenrichment.com
```

El deploy (`deploy-salesnav-prod.sh`) añade esta variable si no existe.

## 4. Comportamiento en código

`/api/salesnav-connect.php` pide el link a Unipile y reescribe el host:

- `account.unipile.com` → `connect.companydataenrichment.com`
- `auth.unipile.com` → `connect.companydataenrichment.com`

El usuario vuelve a `https://companydataenrichment.com/salesnav/?connected=1` tras conectar.

## 5. Prueba end-to-end

1. Confirmar CNAME activo y dominio habilitado en Unipile.
2. Ir a https://companydataenrichment.com/salesnav/
3. **Connect LinkedIn** → la barra de direcciones debe mostrar `connect.companydataenrichment.com`, no `account.unipile.com`.
