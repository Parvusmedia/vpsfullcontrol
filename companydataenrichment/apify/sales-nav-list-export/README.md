# Sales Navigator List Export — Full Profile (Harvest)

Apify Actor para exportar listas o búsquedas de **LinkedIn Sales Navigator** con **perfil completo** vía [HarvestAPI](https://harvestapi.io).

**No incluye email.** Solo export SN + enriquecimiento de perfil (mismo tier *Enriched* de CompanyDataEnrichment).

## Pipeline

```
Sales Navigator URL  →  Unipile (lista/búsqueda)  →  Harvest (perfil + empresa)  →  Dataset CSV
```

| Paso | API | Qué hace |
|------|-----|----------|
| 1 | **Unipile** | Pagina la lista o búsqueda SN del seat conectado |
| 2 | **Harvest** | Por cada `linkedin_url`: perfil completo + empresa actual |
| 3 | Output | 20 columnas (basic + enriched), sin `work_email` |

## Columnas de salida

**Basic (Unipile):** `first_name`, `last_name`, `full_name`, `job_title`, `company_name`, `location`, `linkedin_url`, `sales_nav_id`, `open_profile`, `connection_degree`

**Enriched (Harvest):** `company_linkedin_url`, `company_domain`, `company_industry`, `company_size`, `company_hq`, `seniority`, `tenure_years`, `profile_summary`, `skills`, `languages`

## Input

| Campo | Descripción |
|-------|-------------|
| `mode` | `list` o `search` |
| `listUrl` / `searchUrl` | URL de Sales Navigator |
| `maxLeads` | 1–2000 |
| `unipileApiKey` + `unipileAccountId` | Export SN |
| `harvestApiKey` | Enriquecimiento perfil completo |
| `harvestBatchSize` | Paralelismo Harvest (default 10) |

## Qué NO hace

- No busca email (`work_email`, Icypeas, etc.)
- No tier “Mail” — eso queda solo en el producto web CDE si lo activáis aparte

## Desarrollo local

```bash
cd companydataenrichment/apify/sales-nav-list-export
npm install
npm test
apify run --input-file=input.example.json
```

## Publicar

```bash
apify login
apify push
```

Pricing: ver [PRICING.md](./PRICING.md) — fijo (seat Unipile) + uso por lead enriquecido (incluye coste Harvest).

## Código PHP equivalente

| PHP | Actor |
|-----|-------|
| `cde_salesnav_export()` | `exportLeads()` |
| `cde_salesnav_flatten_lead()` | `flattenLead()` |
| `cde_harvest_enrich_rows()` | `enrichRows()` |
