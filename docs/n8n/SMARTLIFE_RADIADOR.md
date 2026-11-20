# Smart Life — radiador buhardilla (Luca)

Workflow en n8n Cloud: [HPaa9jGQmpDex41t](https://pmedia.app.n8n.cloud/workflow/HPaa9jGQmpDex41t)

## Requisito: API REST

El token MCP (JWT) **no** permite leer ejecuciones ni actualizar este workflow. Añade en el Cloud Agent:

- `N8N_REST_API_KEY` — clave con prefijo `n8n_api_...` (n8n → Settings → API)

## Diagnosticar y corregir ejecución fallida

```bash
# Solo diagnóstico (ej. ejecución 508599)
python3 scripts/n8n_smartlife_radiador_fix.py --execution-id 508599 --dry-run

# Aplicar parches + workflow de alertas
python3 scripts/n8n_smartlife_radiador_fix.py --execution-id 508599 --apply
```

El script:

1. Lee la ejecución con `includeData=true` y extrae nodo/mensaje de error.
2. Aplica parches seguros (expresiones `$json` → `$input.item.json`, reintentos en Smart Life, timezone `Europe/Madrid`).
3. Crea o actualiza **SmartLife Buhardilla — alertas error** y lo enlaza en `settings.errorWorkflow`.

## Alertas Telegram / WhatsApp

Variables opcionales al ejecutar el script con `--apply`:

| Variable | Uso |
|----------|-----|
| `SMARTLIFE_NOTIFY_TELEGRAM_CHAT_ID` o `TELEGRAM_CHAT_ID` | Chat ID destino |
| `SMARTLIFE_NOTIFY_WHATSAPP_TO` | Número internacional (ej. `+34...`) |
| `TWOCHAT_CREDENTIAL_ID` | ID credencial HTTP Header Auth (2Chat) en n8n |
| `TWOCHAT_FROM_NUMBER` | Número emisor 2Chat (variable de entorno en n8n) |
| `SMARTLIFE_NOTIFY_CHANNEL` | `telegram`, `whatsapp` o `both` (default `both`) |

Telegram reutiliza la credencial `telegramApi` si ya existe en el workflow del radiador.

## Comandos REST auxiliares

```bash
scripts/n8n execution --execution-id 508599 --include-data
scripts/n8n executions --workflow-id HPaa9jGQmpDex41t --status error --limit 10
```