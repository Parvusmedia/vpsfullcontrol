# Movistar Para Ti

Demo de **commerce + alertas personalizadas** en Telegram. El catálogo vive en **NocoDB** (CMS); no hay scraper.

## Arquitectura

```text
NocoDB (movistar_products, movistar_alerts, movistar_events)
        ↓
FastAPI backend (poll cambios cada 60s)
        ↓
Telegram Bot @Movistarparatibot
        ↓
Usuario
```

## Setup NocoDB

Base: `pzyr6ncnc9dk4h0` en `https://mpa.parvusmedia.com`

| Tabla | ID |
|-------|-----|
| movistar_products | `mjzz3jl42nwvod7` |
| movistar_alerts | `mfuk1c0i5m5tavf` |
| movistar_events | `me58xa9thqhplv3` |

```bash
cd backend
pip install -r requirements.txt
python scripts/provision_nocodb.py   # solo si faltan tablas
```

## Variables

Ver `backend/.env.example`.

## Desarrollo local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8020
```

## VPS

- Ruta: `/opt/apps/movistar-parati`
- Puerto: `8020`
- systemd: `movistar-parati-api`
- Polling alternativo: `movistar-parati-polling` (si no hay HTTPS webhook)

## Telegram

El token vive **solo** en el servidor:

```bash
ssh parvus-vps 'nano /opt/apps/movistar-parati/backend/.env'
# TELEGRAM_BOT_TOKEN=...
sudo systemctl restart movistar-parati-api movistar-parati-polling
```

No commitear el token. `@Movistarparatibot` — modo **polling** activo hasta tener HTTPS (webhook).

## Panel de operación (demo)

- **Panel:** https://movistarparati.pmediaplus.com/panel (sesión automática por cookie al abrir la URL)
- **CMS NocoDB:** https://mpa.parvusmedia.com/nc/pzyr6ncnc9dk4h0/vwzlxuhc0956ijho/movistar_products-movistar_products
- La clave `ADMIN_API_KEY` en `backend/.env` protege las APIs admin; el panel la usa vía cookie HttpOnly (no hace falta pegarla manualmente)

DNS: registro `movistarparati.pmediaplus.com → 87.106.194.137` en Plesk (servidor DNS `82.223.3.205`).

1. Usuario crea alerta en Telegram
2. Cambias `monthly_price` en NocoDB (o botón contextual en el panel admin)
3. En ≤15s (demo) o ≤60s (prod) el poll detecta el cambio → Telegram notifica

### Telegram: polling vs webhook

| Modo | Uso | Comando |
|------|-----|---------|
| Polling | Demo / desarrollo | `sudo systemctl start movistar-parati-polling` |
| Webhook | Producción (HTTPS) | `python scripts/setup_telegram_webhook.py` (parar polling antes) |

Endpoint webhook: `POST /api/telegram/webhook` (header `X-Telegram-Bot-Api-Secret-Token`).

Perfil del bot: `python scripts/setup_telegram_profile.py`

Con `DEMO_MODE=true`, el poll efectivo es de **15 s**.

## Futuro producción

Catálogo real vía API/feed/PIM Movistar — ver interfaz `NocoDBProductSource` en `app/services/product_service.py`.

**Concept Demo — Not Live Movistar Data**
