# flightsdemobot

Telegram demo bot **@flightsdemobot** — Saudia fare search (Parvus Media, not official Saudia).

## Features

- Access key gate (shareable demo key)
- English / Arabic UI
- Saudi hub buttons + free IATA entry
- Private chats only
- Dates in Asia/Riyadh (Gregorian)
- Exact dates + same-length trip ±3 days
- Max price in SAR

## VPS layout

- App: `/opt/apps/flightsdemobot`
- Env: `/etc/flightsdemobot/app.env`
- Data: `/var/lib/flightsdemobot`
- Service: `flightsdemobot.service`

Does **not** modify fly456 or any other product.

## Local run

```bash
cd flightsdemobot
cp app.env.example .env
# edit .env: TELEGRAM_BOT_TOKEN, ACCESS_KEY, MOCK_QUOTES=1 for offline tests
export $(grep -v '^#' .env | xargs)
export DATA_DIR=/tmp/flightsdemobot-data
bash scripts/run.sh
```

## Deploy (VPS)

1. Set `/etc/flightsdemobot/app.env` with `TELEGRAM_BOT_TOKEN` and `ACCESS_KEY`.
2. GitHub Actions → **deploy-flightsdemobot** → Run workflow  
   or on the VPS: `sudo bash /opt/apps/flightsdemobot/scripts/install-vps.sh`

## Optional Amadeus

Set `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` in env for live GDS quotes when egress allows.
