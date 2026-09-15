# AI Project Radar

MVP that replicates a manual ChatGPT workflow:

**Search sources → Normalize → OpenAI scoring → Deduplicate → Telegram**

No web frontend. Telegram is the interface. No scraping — only search APIs behind a `SearchProvider` interface.

## What it does

Every hour (and on `/scan`) it:

1. Runs site-specific web searches (Upwork, Freelancer, LinkedIn) for AI automation / n8n / Make / CRM / AdTech / MarTech work.
2. Normalizes URLs and stores them in SQLite.
3. Scores each new opportunity with OpenAI Structured Outputs against a senior automation-consultant profile.
4. Sends Telegram alerts **only if score ≥ 8**.
5. Lets you generate a 150–180 word cover letter from the alert.

Geography: deprioritize/exclude India, Pakistan, Bangladesh. Prefer US, UK, UAE, KSA, Western Europe, Nordics, AU, SG.

Budget preference (not a hard filter): fixed ≥ 2500 USD/EUR, hourly ≥ ~45 EUR, day rate ≥ 500 EUR. Missing budget is estimated by the model.

## Quick start (mocks, no API spend)

```bash
cd ai-project-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# leave keys empty
echo "USE_MOCKS=true" >> .env
echo "ENABLE_SCHEDULER=false" >> .env
echo "ENABLE_TELEGRAM_POLLING=false" >> .env

python -m app scan --mocks
python -m pytest
```

HTTP API (optional):

```bash
USE_MOCKS=true ENABLE_SCHEDULER=false ENABLE_TELEGRAM_POLLING=false \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -X POST http://127.0.0.1:8000/scan
curl http://127.0.0.1:8000/health
```

## Live mode

Fill `.env`:

```
OPENAI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
SEARCH_API_KEY=...          # Serper by default
SEARCH_PROVIDER=serper      # serper | tavily | bing | mock
USE_MOCKS=false
```

Create a bot with [@BotFather](https://t.me/BotFather), then talk to it and read your chat id (e.g. via `@userinfobot`). Only that chat is authorized.

```bash
python -m app serve
```

Or Docker:

```bash
docker compose up --build
```

## Telegram

Commands:

| Command | Action |
|---|---|
| `/scan` | Run the radar immediately |
| `/latest` | Last opportunities with score ≥ 8 |
| `/stats` | scanned today / qualified / sent / applied / discarded |

Alert buttons: **View**, **Prepare proposal**, **Discard**.

After a proposal: **Rewrite**, **Applied**, **Discard**.

## Search providers

`app/search/base.py`:

```python
class SearchProvider:
    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        ...
```

Switch with `SEARCH_PROVIDER`. Serper is the default live source (`tbs=qdr:d` / `qdr:w`). Tavily and Bing are implemented the same way. Queries are generated in `app/search/queries.py` (site-specific templates, rotated each hour).

## Scoring

OpenAI Structured Outputs return:

`score`, `title`, `company`, `country`, `published_at`, `budget`, `estimated_value`, `summary`, `why_fit`, `risks`, `recommendation`, `urgency`.

Weights (prompt): 25% profile fit, 20% economic potential, 15% buyer market, 15% execute, 10% consulting component, 10% competition, 5% freshness.

## Layout

```
ai-project-radar/
  app/               FastAPI + pipeline
  tests/             mocks, no live APIs
  Dockerfile
  docker-compose.yml
  .env.example
```

SQLite lives at `data/radar.db` (configurable via `DATABASE_PATH`).

## Out of scope (intentionally)

Dashboard, auth, multi-user, scraping/job-board crawlers, complex infra.
