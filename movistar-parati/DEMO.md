# DEMO — Movistar Para Ti (5 minutos)

## 1. Abrir Telegram
Busca `@Movistarparatibot` y envía `/start`.

## 2. Explorar catálogo
- **Móviles** → **Todas las marcas** → se abre el listado completo (pager con `1/5`, `2/5`…)
- O elige marca / filtro de precio: **< 10 €/mes**, **10–20 €/mes**, **< 15 €/mes**

## 3. Crear alerta
- Navega con ◀️ ▶️ hasta un producto (p. ej. Pixel 9)
- Pulsa **🔔 Avísame** → elige tipo de aviso (bajada de cuota, precio, etc.)

## 4. Abrir panel
`https://movistarparati.pmediaplus.com/panel`

La sesión se crea **automáticamente** al abrir la URL (cookie HttpOnly). No hace falta pegar ninguna clave.

**CMS NocoDB:** https://mpa.parvusmedia.com/nc/pzyr6ncnc9dk4h0/vwzlxuhc0956ijho/movistar_products-movistar_products

En Catálogo, activa **Solo con avisos** para ver qué productos tienen usuarios esperando notificación.

## 5. Simular bajada de precio
En el catálogo del panel, botón contextual del producto (p. ej. Pixel 9 → **Bajar a 8 €/mes**).

O edita la cuota manualmente y **Guardar en NocoDB**.

## 6. Recibir push
El usuario recibe Telegram en segundos (poll cada ~60 s, o **Forzar detección** en el panel).

## 7. Actividad y métricas
- **Avisos** — alertas activas por usuario
- **Actividad** — eventos de cambio de catálogo
- Métricas en la cabecera del panel (activos, destacados, novedades…)

## Telegram: polling vs webhook

| Modo | Cuándo | Cómo |
|------|--------|------|
| **Polling** | Demo / desarrollo | `systemctl start movistar-parati-polling` |
| **Webhook** | Producción (HTTPS) | Ver `backend/scripts/setup_telegram_webhook.py` |

Con HTTPS en `movistarparati.pmediaplus.com` ya puedes migrar a webhook:

```bash
ssh parvus-vps
sudo systemctl stop movistar-parati-polling
cd /opt/apps/movistar-parati/backend && . .venv/bin/activate
python scripts/setup_telegram_webhook.py
sudo systemctl restart movistar-parati-api
```
