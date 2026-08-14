# n8n en una sola conversación (MCP + REST)

Objetivo: usar un único comando local y que el script elija automáticamente MCP o REST según el token disponible.

## Secrets recomendados

- `N8N_URL` (ej: `https://pmedia.app.n8n.cloud`)
- `N8N_MCP_TOKEN` (JWT con `aud: mcp-server-api`)
- `N8N_REST_API_KEY` (API key REST de n8n, normalmente prefijo `n8n_api_`)

Compatibilidad legacy:

- Si solo existe `N8N_API_KEY`, el script intenta inferir el tipo:
  - JWT (`a.b.c`) => MCP
  - `n8n_api_...` => REST

## Comando único

```bash
python3 scripts/n8n_unified.py <comando>
```

Comandos disponibles:

- `status`: valida conectividad y tipo de token disponible.
- `list [--limit 50] [--query texto]`: lista workflows.
- `details --workflow-id <id>`: muestra detalle.
- `export [--out ruta]`: exporta workflows a JSON.

## Ejemplos

```bash
python3 scripts/n8n_unified.py status
python3 scripts/n8n_unified.py list --limit 20
python3 scripts/n8n_unified.py details --workflow-id m1eDecjWiX7Ml7J6
python3 scripts/n8n_unified.py export --out /workspace/n8n_export_latest
```

## Comportamiento de export

- Si hay REST válido: exporta por `/api/v1/workflows` (más completo).
- Si no hay REST y sí MCP válido: exporta lo visible por MCP.
