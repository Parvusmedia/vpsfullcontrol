# Ngaged

Panel de **employee advocacy**: campañas LinkedIn, invitaciones por email (Repostear / Ignorar), dashboard con métricas y repost one-click para el equipo.

## Producto (lo que ve el usuario)

- **Dashboard** — campañas enviadas, alcance, reposts, tasa de adopción y gráficos.
- **Campañas** — URL de LinkedIn, vista previa, selección de miembros y envío.
- **Miembros** — email + cuenta LinkedIn asociada (empleados solo vinculan vía `/conectar` y responden por email).

Marca única: **Ngaged** en UI y emails.

## Requisitos técnicos

- PHP 8.1+ (`curl`, `json`)
- Cuenta LinkedIn conectada vía API de publicación (clave en entorno del servidor)
- Cuentas de administrador (email + contraseña) con sesión persistente; login opcional con Google

## Local

```bash
export PUBLORA_API_KEY=sk_...
export NGAGED_ADMIN_KEY=demo-admin
cd gaggle-demo
php -S 127.0.0.1:8787 -t public public/router.php
```

Panel: http://127.0.0.1:8787/login — crea el primer admin con `php deploy/create-admin.php tu@email.com 'contraseña-larga'`.

## VPS — https://ngaged.pmediaplus.com

Ver [deploy/deploy-demo.sh](deploy/deploy-demo.sh) y [deploy/install-ngaged-vhost.sh](deploy/install-ngaged-vhost.sh).

### Ops (mantenedores)

Rutas en servidor (nombres históricos):

| Qué | Dónde |
|-----|--------|
| App | `/opt/apps/gaggle-demo` |
| Secrets | `/opt/apps/private/gaggle-demo/publora.env` |
| Datos JSON | `/opt/apps/private/gaggle-demo/data` |
| systemd | `gaggle-demo.service` → `:8790` |

Variables en `publora.env` (ejemplo ampliado en [deploy/publora.env.example](deploy/publora.env.example) y [deploy/mail.env.example](deploy/mail.env.example)):

```
PUBLORA_API_KEY=sk_...
NGAGED_ADMIN_KEY=...
NGAGED_APP_URL=https://ngaged.pmediaplus.com
NGAGED_MAIL_FROM="Ngaged <noreply@pmediaplus.com>"
NGAGED_SIGNING_SECRET=...
```

DNS: [deploy/dns-ngaged-pmediaplus.sh](deploy/dns-ngaged-pmediaplus.sh) (A `ngaged` → Parvus).

### Datos de demo (presentaciones)

Para rellenar miembros, equipos y campañas con historial de envíos (el dashboard deja de mostrar la capa «Datos demo»):

```bash
# En el VPS (datos en /opt/apps/private/gaggle-demo/data)
ssh parvus-vps 'cd /opt/apps/gaggle-demo && php deploy/seed-demo-data.php --force'
```

En **Ajustes** puedes revisar el semáforo del sistema y fusionar miembros duplicados por email.

## API (resumen)

| Ruta | Uso |
|------|-----|
| `GET /api/stats?days=30` | Dashboard (admin) |
| `POST /api/campaigns` | Crear campaña |
| `POST /api/dispatch` | Enviar emails |
| `POST /api/preview-post` | URL → URN + OG |
| `GET/POST /api/members` | CRUD miembros |
| `GET /api/action` | Enlaces email (`/go?token=…`) |

## Seguridad

Demo orientada a equipos internos: protege la URL (VPN, Basic Auth, allowlist) antes de producción real.
