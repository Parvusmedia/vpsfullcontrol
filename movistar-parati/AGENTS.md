# AGENTS.md — Movistar Para Ti

## Stack

- **NocoDB** `https://mpa.parvusmedia.com` — base `pzyr6ncnc9dk4h0`
  - `movistar_products` → `mjzz3jl42nwvod7`
  - `movistar_alerts` → `mfuk1c0i5m5tavf`
  - `movistar_events` → `me58xa9thqhplv3`
- **FastAPI** — backend puerto 8020
- **Telegram** — `@Movistarparatibot`
- **VPS** — `/opt/apps/movistar-parati`, usuario `cursorbot`

## NocoDB URLs

- Base: https://mpa.parvusmedia.com/dashboard/#/nc/pzyr6ncnc9dk4h0
- Productos: https://mpa.parvusmedia.com/dashboard/#/nc/pzyr6ncnc9dk4h0/mjzz3jl42nwvod7

## Comandos

```bash
# Provision tablas NocoDB
cd backend && python scripts/provision_nocodb.py

# Deploy VPS
./scripts/deploy.sh

# Polling Telegram (demo; parar antes de activar webhook)
sudo systemctl start movistar-parati-polling

# Webhook Telegram (producción con HTTPS)
cd backend && python scripts/setup_telegram_webhook.py
```

## Reglas

- No scraper Movistar
- NocoDB = única fuente de catálogo
- No hardcodear tokens; usar `.env`
- Poll de cambios comerciales cada 60s (configurable)
