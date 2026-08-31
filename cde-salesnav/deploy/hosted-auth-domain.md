# White-label LinkedIn connect — `connect.companydataenrichment.com`

Opción 2: subdominio propio para el wizard de Unipile Hosted Auth (sin iframe).

## 1. DNS (registrar / Cloudflare / Plesk)

Crear un registro **CNAME**:

| Campo   | Valor                    |
|---------|--------------------------|
| Name    | `connect`                |
| Type    | `CNAME`                  |
| Target  | `account.unipile.com`    |
| TTL     | Auto o 300s              |

Verificar propagación:

```bash
dig +short connect.companydataenrichment.com CNAME
# debe devolver: account.unipile.com.
```

**Importante:** no apuntar el subdominio al VPS de Parvus. Unipile sirve el wizard y el certificado SSL en su infra.

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
