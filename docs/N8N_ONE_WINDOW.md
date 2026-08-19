# n8n en una sola conversación (MCP + REST)

Objetivo: usar un único comando local y que el script elija automáticamente MCP o REST según el token disponible.

## Configuración local (recomendada)

1. Copia la plantilla:

```bash
cp config/n8n.local.env.example config/n8n.local.env
```

2. Rellena `N8N_API_KEY` en `config/n8n.local.env` (archivo **gitignored**).

Los scripts cargan ese archivo automáticamente si las variables no están ya en el entorno.

## Cursor Cloud Agent / otro entorno

Añade estos secrets en el dashboard del Cloud Agent (o exporta las mismas variables):

- `N8N_URL` = `https://pmedia.app.n8n.cloud`
- `N8N_API_KEY` = tu JWT `public-api` o clave `n8n_api_...`

Opcional para MCP (token distinto, `aud: mcp-server-api`):

- `N8N_MCP_TOKEN`
- `N8N_MCP_ENDPOINT` = `https://pmedia.app.n8n.cloud/mcp-server/http`

## Secrets soportados

- `N8N_URL` (ej: `https://pmedia.app.n8n.cloud`)
- `N8N_API_KEY` — JWT `public-api` o clave REST (`n8n_api_...`)
- `N8N_REST_API_KEY` — opcional si difiere de `N8N_API_KEY`
- `N8N_MCP_TOKEN` — JWT con `aud: mcp-server-api` (solo para MCP)

Compatibilidad legacy en `scripts/n8n_unified.py`:

- Si solo existe `N8N_API_KEY`, el script intenta usarlo para REST y MCP según el formato.

## Comando único

```bash
scripts/n8n status
scripts/n8n list --limit 20
scripts/n8n details --workflow-id sFefLQ6Js3pPV3oB
```

## Deploy de workflows

Registro: [`config/n8n-deploy.json`](../config/n8n-deploy.json)

```bash
python3 scripts/deploy_n8n_workflows.py
# o solo LinkedIn hiring:
python3 scripts/deploy_linkedin_applicants_workflow.py
```

## Workflows en este repo

| Nombre | ID n8n | Archivo |
|--------|--------|---------|
| LinkedIn Hiring Applicants AI | `sFefLQ6Js3pPV3oB` | `n8n/workflows/linkedin-hiring-applicants-ai.json` |

## Comportamiento de export

- Si hay REST válido: exporta por `/api/v1/workflows` (más completo).
- Si no hay REST y sí MCP válido: exporta lo visible por MCP.
