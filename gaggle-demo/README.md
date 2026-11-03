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

**DNS:** el registro **A** de `ngaged.pmediaplus.com` debe apuntar al VPS Parvus (`87.106.194.137`, igual que `prosegur.pmediaplus.com`). Si apunta a otra IP, Let's Encrypt y el sitio público no funcionarán.

```bash
./gaggle-demo/deploy/deploy-demo.sh
ssh parvus-vps 'bash /opt/apps/gaggle-demo/deploy/install-ngaged-vhost.sh'
```

Copia a `/opt/apps/gaggle-demo` en `parvus-vps`. Crea `/opt/apps/private/gaggle-demo/publora.env` con:

```
PUBLORA_API_KEY=sk_...
GAGGLE_DEMO_ADMIN_KEY=elige-una-clave-larga
```

Sirve con nginx/apache apuntando al `public/` o PHP built-in detrás de systemd (ver comentarios en `deploy-demo.sh`).

## Seguridad (demo)

No es producción: sin OAuth por empleado ni multi-tenant. Protege la URL (VPN, Basic Auth, IP allowlist) antes de exponerla.
