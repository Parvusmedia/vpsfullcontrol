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

```bash
cd backend
pip install -r requirements.txt
# Token desde /opt/apps/fly456bot/.env o variable de entorno
python scripts/provision_nocodb.py
```

Copia los `NOCODB_*_TABLE_ID` generados a `.env`.

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

## Demo en vivo

1. Usuario crea alerta en Telegram
2. Cambias `monthly_price` en NocoDB (o botón **Simular bajada** en `/movistar-demo/admin`)
3. En ≤60s el poll detecta el cambio → Telegram notifica

## Futuro producción

Catálogo real vía API/feed/PIM Movistar — ver interfaz `NocoDBProductSource` en `app/services/product_service.py`.

**Concept Demo — Not Live Movistar Data**
