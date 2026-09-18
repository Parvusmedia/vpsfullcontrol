# Meta Ads desde Cursor (MCP)

Gestiona campañas de Meta (Facebook/Instagram) con instrucciones en Cursor, sin abrir Ads Manager. El puente es el servidor MCP en [`meta-ads-mcp/`](../meta-ads-mcp/).

## Secrets (Cursor Environment o `meta-ads-mcp/.env` local)

Nunca commitear el token.

```env
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=act_149543758710373
META_APP_ID=1418774567014992
META_API_VERSION=v21.0
META_BUDGET_CHANGE_MAX_PCT=20
```

`page_id` y `pixel_id` **no** van en env: indícalos en cada campaña en el chat (o elige tras `meta_ads_list_pages` / `meta_ads_list_pixels`).

## Registrar MCP en Cursor

1. Build: `cd meta-ads-mcp && npm install && npm run build`
2. En **Cursor → Environment → Secrets**, define `META_ACCESS_TOKEN`.
3. Usa [`.cursor/mcp.json`](../.cursor/mcp.json) (servidor `meta-ads`) o añade la misma entrada en tu MCP local.

## Reglas para el agente

- Herramientas `meta_ads_*` únicamente para Meta Ads.
- **Escrituras:** mostrar plan exacto y exigir confirmación del usuario; llamar herramientas con `confirmed: true` solo después.
- Crear en **`PAUSED`** salvo que el usuario pida activar y confirme `allow_active_on_create`.
- No asumir `page_id` / `pixel_id`; pedirlos o listar activos.
- No imprimir tokens ni URLs de paging con `access_token`.

## Objetivos habituales

| Objetivo | `objective` | Ad set |
|----------|-------------|--------|
| Leads | `OUTCOME_LEADS` | `optimization_goal=LEAD_GENERATION`, `page_id`, formulario (`lead_gen_form_id`) |
| Conversiones | `OUTCOME_SALES` | `pixel_id` + `custom_event_type` (p. ej. `PURCHASE`) |
| Tráfico | `OUTCOME_TRAFFIC` | según destino |

## Smoke test (solo lectura)

```bash
cd meta-ads-mcp
cp .env.example .env   # rellenar META_ACCESS_TOKEN
./scripts/smoke-read.sh
```

Comprueba cuenta, funding, campañas, páginas, pixels e insights (salida sin tokens).

## Ejemplos de prompts

- «Lista campañas activas y el spend de los últimos 7 días.»
- «Pausa la campaña X y baja el presupuesto del ad set Y un 15 %.»
- «Crea campaña de leads PAUSED: page_id …, presupuesto 20 €/día, formulario …»
- «Sugiere optimizaciones con CPA máximo 40 € en los últimos 14 días.»

## Rotación de token

Si el token se expuso en chat o logs, regenera el token del system user en Meta Business y actualiza `META_ACCESS_TOKEN`.
