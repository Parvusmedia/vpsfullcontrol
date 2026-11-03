# Gaggle Demo (employee advocacy + Publora)

Demo mínimo tipo **GaggleAMP**: marketing crea actividades; los miembros las aprueban con un clic y Publora publica en LinkedIn.

## Flujo

1. **Admin** — crea actividad (post nuevo o repost con URN + comentario opcional) y elige cuentas destino (desde Publora).
2. **Miembro** — ve la cola, elige su identidad (conexión LinkedIn) y pulsa **Compartir ahora** o **No gracias**.
3. **Publora** — `publishNow` o repost vía `platformSettings.linkedin`.

## Requisitos

- PHP 8.1+ con `curl` y `json`
- API key Publora (`sk_…`) con al menos una conexión LinkedIn
- Opcional: clave admin (`GAGGLE_DEMO_ADMIN_KEY`) para crear actividades

## Local

```bash
export PUBLORA_API_KEY=sk_...
export GAGGLE_DEMO_ADMIN_KEY=demo-admin   # opcional; por defecto demo-admin
cd gaggle-demo
php -S 127.0.0.1:8787 -t public public/router.php
```

- Panel: http://127.0.0.1:8787/
- Admin key en el formulario admin (localStorage)

## VPS (Parvus) — https://ngaged.pmediaplus.com

**DNS:** la zona `pmediaplus.com` vive en **Plesk (nextconvers-vps / 82.223.3.205)**. El **A** de `ngaged` debe ser **`87.106.194.137`** (Parvus, nginx + app).

```bash
./gaggle-demo/deploy/dns-ngaged-pmediaplus.sh   # Plesk: ngaged → Parvus
./gaggle-demo/deploy/deploy-demo.sh
ssh parvus-vps 'bash /opt/apps/gaggle-demo/deploy/install-ngaged-vhost.sh'
ssh parvus-vps 'sudo certbot --nginx -d ngaged.pmediaplus.com'  # tras DNS OK
```

Copia a `/opt/apps/gaggle-demo` en `parvus-vps`. Crea `/opt/apps/private/gaggle-demo/publora.env` con:

```
PUBLORA_API_KEY=sk_...
GAGGLE_DEMO_ADMIN_KEY=elige-una-clave-larga
```

Sirve con nginx/apache apuntando al `public/` o PHP built-in detrás de systemd (ver comentarios en `deploy-demo.sh`).

## Seguridad (demo)

No es producción: sin OAuth por empleado ni multi-tenant. Protege la URL (VPN, Basic Auth, IP allowlist) antes de exponerla.
