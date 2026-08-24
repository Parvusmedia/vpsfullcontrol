# Movistar Para ti

Plataforma demo de commerce + demanda + alertas en Telegram.

## Componentes

- **API** FastAPI (`8020`)
- **Bot** `@Movistarparatibot` (webhook)
- **Mini App** `/app`
- **Demo Control** `/panel`

## Setup VPS

1. Crear DB Postgres:

```bash
sudo -u postgres psql -c "CREATE USER movistar_parati WITH PASSWORD '...';"
sudo -u postgres psql -c "CREATE DATABASE movistar_parati OWNER movistar_parati;"
```

2. Copiar `.env.example` → `.env` en `/opt/apps/movistar-parati/backend/`
3. Configurar `TELEGRAM_BOT_TOKEN`, `PUBLIC_BASE_URL` (HTTPS), `ADMIN_API_KEY`
4. `./scripts/deploy.sh`
5. Configurar nginx + SSL apuntando a `127.0.0.1:8020`
6. Registrar webhook:

```bash
curl -X POST https://TU_DOMINIO/api/telegram/setup-webhook -H "X-Admin-Key: TU_KEY"
```

## Disclaimer

Concept Demo — Not Live Movistar Data
