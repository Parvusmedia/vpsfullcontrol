# Education AI Advisor (English demo)

International English replica of the USJ display-advising demo for non-Spanish-speaking prospects.

**Domain:** https://educationdemo.pmediaplus.com

| Route | Purpose |
|-------|---------|
| `/` | Concept hub (step 1) |
| `/ad/` | Live IAB creatives 300×600 + 970×250 (step 2) |
| `/admissions` | Lead destination — CRM + WhatsApp mockup (step 3) |
| `/orientador` | Full-page advisor reference |
| `/admin` | Programme catalogue |
| `/debug` | Event funnel |

Spanish demo remains at https://usjdemo.pmediaplus.com (separate service on port 8021).

## Stack

- Static frontend (`frontend/`) + FastAPI API on `127.0.0.1:8022`
- nginx TLS + proxy (same VPS as USJ demo)
- `AI_MODE=mock` by default (no OpenAI key required)

## Local dev

```bash
cd education-ai-advisor/backend
export EDU_FRONTEND_DIR=/workspace/education-ai-advisor/frontend
export AI_MODE=mock
uvicorn main:app --host 127.0.0.1 --port 8022
```

Or Docker: `docker compose up` → http://127.0.0.1:8091

## Deploy (VPS)

```bash
EDU_ADVISOR_DOMAIN=educationdemo.pmediaplus.com EDU_ADVISOR_PORT=8022 \
  sudo scripts/deploy.sh
```

DNS: A record `educationdemo.pmediaplus.com → 87.106.194.137` (Plesk script in `scripts/plesk-add-a-record.sh` with `DNS_HOST=educationdemo`).

## Branding

- Institution: **Demo University** (generic sales demo, not a real client)
- Product line: **Advising in display**
- JS namespace: `EDU` (session keys `edu_state`, `edu_events`)

## Tests

```bash
python3 -m pytest education-ai-advisor/tests -q
```
