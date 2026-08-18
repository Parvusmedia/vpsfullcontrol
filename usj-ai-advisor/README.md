# USJ AI Student Advisor

Interactive HTML5 ad that behaves as a **mini academic advisor**, not a DCO template and not a generic chatbot.

> Traditional university advertising asks: *Are you interested in this master's?*
> AI Student Advisor asks: *Where are you today and where you want to go?*

That turns anonymous traffic into **context-rich prospects** before Admissions speaks to anyone.

**Domain:** `https://usjdemo.pmediaplus.com`

`usj.pmediaplus.com` already hosts another app. This demo is served at `usjdemo.pmediaplus.com`.

| Recurso | URL |
|---------|-----|
| Advisor | https://usjdemo.pmediaplus.com/ |
| Ad 300×600 | https://usjdemo.pmediaplus.com/ad |
| Admissions | https://usjdemo.pmediaplus.com/admissions |
| Catalogue | https://usjdemo.pmediaplus.com/admin |
| Debug events | https://usjdemo.pmediaplus.com/debug |
| Health | https://usjdemo.pmediaplus.com/api/health |

## Product positioning

Not an AI chatbot. Not DCO.

**AI Student Advisor** = advertising + career guidance + programme discovery + lead qualification.

Message: *AI Student Advisor — from the first impression.*

## Architecture

```text
opciones guiadas (3 preguntas)
    → perfil estructurado (sin PII)
    → motor de reglas + eliminaciones
    → 1, 2 o 3 másteres restantes
    → etiquetas de elegibilidad del catálogo
    → explicación (plantillas | LLM opcional, solo hechos del catálogo)
    → lead cualificado
```

The LLM **never** decides academic requirements, modality, price, places, dates or admission.

```text
DV360 HTML5
    → AI Advisor API (this service)
    → programme catalogue (JSON)
    → rules engine
    → optional LLM
```

Future RAG (not implemented): USJ programme pages → approved content → knowledge base → answers. The model may only use approved facts already stored on each programme.

## Modes

`AI_MODE=mock` (default, no API keys). Keyword parser + scoring + catalogue Q&A.

`AI_MODE=openai` later: `OPENAI_API_KEY` stays on the server. On any LLM error the engine falls back to mock. Never put keys in JavaScript.

## Match score

Documented weights in `backend/data/programmes.json`:

| Signal | Weight |
|--------|--------|
| Education match | 30% |
| Professional area | 20% |
| Career goal | 20% |
| Interests | 15% |
| Modality constraints | 10% |
| Experience | 5% |

Priority chips apply small, documented boosts (e.g. *Learn new technology* → Applied AI). Scores are reproducible. Below `strong_match_threshold` (0.48) the UI **does not force** a recommendation.

Eligibility labels: `BUEN ENCAJE` · `PROBABLEMENTE ELEGIBLE` · `ADMISIÓN A REVISAR`. Never `YOU ARE ACCEPTED`.

## Lead intent

`HIGH` — profile + recommendation + (question or priority or advisor).  
`MEDIUM` — recommendation / programme explore.  
`LOW` — started only.

PII is not collected in the ad. **Seguir por WhatsApp** sends the person to a prefilled WhatsApp message about the recommended master's.

## KPIs this product can measure

Interaction Rate · Profiles Analysed · Recommendations Generated · Average Match Score · Programme Discovery Rate · Questions Asked · High Intent Users · Information Requests · Applications · Lead → Application · Cost per Qualified Prospect.

The goal is not only CTR.

## Local

```bash
cd usj-ai-advisor
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
AI_MODE=mock .venv/bin/uvicorn main:app --app-dir backend --reload --port 8021
# other terminal
python3 -m http.server 8090 --directory frontend
# or: docker compose up
# http://127.0.0.1:8091/
.venv/bin/python -m pytest tests -q
```

CORS is open on the API so a DV360 HTML5 host can call it.

## VPS deploy

Same pattern as other Parvus apps: **nginx + systemd**, API bound to `127.0.0.1:8021`. Docker Compose is local only. No new public ports.

```bash
usj-ai-advisor/scripts/inspect-vps.sh
sudo usj-ai-advisor/scripts/deploy.sh /opt/apps/usj-ai-advisor
```

DNS: Plesk A record `usjdemo.pmediaplus.com → 87.106.194.137`. TLS via `certbot certonly --webroot` (never `--nginx`).

Restart API only:

```bash
sudo systemctl restart usj-ai-advisor.service
```

## Catalogue

Edit `backend/data/programmes.json`, then:

```bash
sudo systemctl restart usj-ai-advisor.service
# or POST /api/admin/reload
```

Future: USJ CMS → programme feed → this JSON → engine. Adding 10, 50 or 100 programmes does not require matcher changes.

## DV360

The `/ad` preview shows IAB frames at **exact** 300×250, 300×600 and 970×250. Each iframe is the live HTML5 unit (`/ad/unit.html?size=`). **Seguir por WhatsApp** opens `api.whatsapp.com` with the selected master's and profile. If `window.clickTag` exists it wraps that URL.

## Tests covered

1. Physiotherapist → Biomechanics  
2. Software + AI → Applied AI  
3. Marketing profile → Marketing  
4. Chef / architect → no forced match  
5. Priority changes ranking  
6. Question uses catalogue facts  
7. Lead stores recommendation context  
8. Admissions reads enriched lead  
9. Mock mode without API keys  
10. API/LLM failure falls back  
11. Mobile-first CSS  
12. 300×600 unit on `/ad`
