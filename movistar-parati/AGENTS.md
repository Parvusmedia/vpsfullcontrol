# AGENTS.md — Movistar Para Ti

## Stack

- **NocoDB** `https://mpa.parvusmedia.com` — catálogo CMS (`movistar_products`, `movistar_alerts`, `movistar_events`)
- **FastAPI** — backend en puerto 8020
- **Telegram** — `@Movistarparatibot`
- **VPS** — `/opt/apps/movistar-parati`, usuario `cursorbot`

## Comandos

```bash
# Provision tablas NocoDB
cd backend && python scripts/provision_nocodb.py

# Deploy VPS
./scripts/deploy.sh

# Polling Telegram (sin webhook HTTPS)
sudo systemctl start movistar-parati-polling
```

## Reglas

- No scraper Movistar
- NocoDB = única fuente de catálogo
- No hardcodear tokens; usar `.env`
- Poll de cambios comerciales cada 60s (configurable)
