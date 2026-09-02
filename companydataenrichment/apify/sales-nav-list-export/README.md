# Sales Navigator List Export (Apify Actor)

Apify Actor que exporta leads de **LinkedIn Sales Navigator** usando la API de **Unipile** — la misma integración que ya usa [CompanyDataEnrichment](https://companydataenrichment.com/salesnav/).

## Por qué Unipile (y no browser scraping)

| Enfoque | Pros | Contras |
|--------|------|--------|
| **Unipile API** (este actor) | Estable, misma lógica que CDE en producción, sin cookies `li_at`, paginación oficial | Requiere cuenta Unipile + seat LinkedIn conectado |
| Browser + cookies | Publicable en Apify Store sin Unipile | Mantenimiento alto, riesgo de ban, compite con decenas de actores existentes |

Este actor es ideal para:

- **Uso interno** (CDE, n8n, Make) vía API de Apify
- **Publicar en Apify Store** como “bring your own Unipile” o empaquetado con tu servicio gestionado

## Input

| Campo | Descripción |
|-------|-------------|
| `mode` | `list` (lista guardada) o `search` (búsqueda people) |
| `listUrl` | URL `/sales/lists/people/...` o ID numérico |
| `searchUrl` | URL `/sales/search/people?...` |
| `maxLeads` | Máximo 1–2000 (default 100) |
| `unipileApiKey` | API key Unipile (o env `UNIPILE_API_KEY`) |
| `unipileAccountId` | `account_id` del seat LinkedIn en Unipile |
| `unipileBaseUrl` | Default `https://api.unipile.com/v2` |
| `pageDelayMs` | Pausa entre páginas (default 1500 ms) |

## Output (dataset)

Columnas alineadas con el CSV de CompanyDataEnrichment:

`first_name`, `last_name`, `full_name`, `job_title`, `company_name`, `location`, `linkedin_url`, `sales_nav_id`, `open_profile`, `connection_degree`

## Desarrollo local

```bash
cd companydataenrichment/apify/sales-nav-list-export
npm install
npm test

# Run con Apify CLI (necesitas cuenta Apify)
export APIFY_TOKEN=...
apify run --input-file=input.example.json
```

Ejemplo `input.example.json`:

```json
{
  "mode": "list",
  "listUrl": "https://www.linkedin.com/sales/lists/people/YOUR_LIST_ID",
  "maxLeads": 50,
  "unipileApiKey": "YOUR_UNIPILE_API_KEY",
  "unipileAccountId": "YOUR_UNIPILE_ACCOUNT_ID"
}
```

## Publicar en Apify

```bash
npm install -g apify-cli   # si no lo tienes
apify login
apify push
```

Luego en Apify Console:

1. Configura **secrets** del Actor (`UNIPILE_API_KEY` si no quieres que el usuario los pase).
2. Añade descripción, pricing (pay-per-result recomendado: ~$0.01–0.05/lead según mercado).
3. Opcional: webhook a tu backend CDE para sustituir el worker PHP async.

## Integración con CompanyDataEnrichment

Hoy CDE exporta en PHP vía `cde_salesnav_export()` en `public/api/_unipile.php`. Para mover exports pesados a Apify:

1. `salesnav-tasks.php` arranca un run Apify en lugar de `cde_tasks_run()` local.
2. Webhook Apify → tu API marca task `ready` y guarda dataset CSV.
3. Mantienes créditos/billing en CDE; Apify solo ejecuta el scrape.

Variables en `private/cde/apify.env`:

```
APIFY_TOKEN=...
APIFY_SALESNAV_ACTOR_ID=tu-usuario~sales-nav-list-export
```

## Seguridad

- No commitear API keys ni `account_id` en el repo.
- En Apify Store, marca `unipileApiKey` como secret input.
- El usuario final debe conectar **su** seat SN vía Unipile (hosted auth), igual que en el panel CDE.

## Relación con código PHP

| PHP (`_unipile.php`) | Actor (`src/`) |
|----------------------|----------------|
| `cde_salesnav_flatten_lead` | `flattenLead()` |
| `cde_salesnav_paginate_v2_list` | `paginateV2List()` |
| `cde_salesnav_paginate_v2_search` | `paginateV2Search()` |
| `cde_salesnav_normalize_list_url` | `normalizeSourceUrl()` |
