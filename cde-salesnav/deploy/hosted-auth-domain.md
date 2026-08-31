# White-label LinkedIn connect — `connect.companydataenrichment.com`

Opción 2: subdominio propio para el wizard de Unipile Hosted Auth (sin iframe).

## 1. DNS (registrar / Piensa Solutions)

El dominio usa nameservers públicos **Piensa Solutions** (`ns97.piensasolutions.com`, `ns98.piensasolutions.com`).  
El CNAME también está en **Plesk** del VPS (`82.223.3.205`) para cuando el dominio use DNS local.

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

**Plesk (ya aplicado en el VPS):**

```bash
ssh nextconvers-vps "plesk bin dns --info companydataenrichment.com | grep connect"
# connect.companydataenrichment.com. CNAME account.unipile.com.
```

Consulta directa al DNS del VPS (funciona aunque Piensa aún no propague):

```bash
dig +short connect.companydataenrichment.com CNAME @82.223.3.205
```

**Importante:** no apuntar `connect` al VPS. Unipile sirve el wizard y el certificado SSL.

## 2. Validación en Unipile

1. Entrar al [Unipile Dashboard](https://dashboard.unipile.com) → **Hosted Auth**.
2. En **Hosted auth domain**, enviar el CNAME `connect.companydataenrichment.com`.
3. Esperar a que aparezca en **Enabled domains** (Unipile genera el certificado).
4. Si tarda, contactar soporte Unipile con la URL completa: `https://connect.companydataenrichment.com`.

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
