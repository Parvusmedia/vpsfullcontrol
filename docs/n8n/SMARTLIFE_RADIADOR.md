# Smart Life — radiador buhardilla (Luca)

Workflow en n8n Cloud: [HPaa9jGQmpDex41t](https://pmedia.app.n8n.cloud/workflow/HPaa9jGQmpDex41t)

## Acceso API (Cloud Agent y VPS)

| Origen | Variable | Uso |
|--------|----------|-----|
| Cloud Agent | `N8N_API_KEY` (JWT `aud: mcp-server-api`) | MCP parcial |
| Cloud Agent / VPS | `N8N_REST_API_KEY` o JWT `aud: public-api` | REST (`/api/v1/...`) |
| VPS Parvus | `/opt/apps/nextconvers-qualification-gate/config/deployment.local.env` | `N8N_BASE_URL` + `N8N_API_KEY` (REST) |

`scripts/n8n_unified.py` trata JWT `public-api` como REST.

## Diagnosticar y corregir ejecución fallida

```bash
# Solo diagnóstico (ej. ejecución 508599)
python3 scripts/n8n_smartlife_radiador_fix.py --execution-id 508599 --dry-run

# Aplicar parches + workflow de alertas
python3 scripts/n8n_smartlife_radiador_fix.py --execution-id 508599 --apply
```

### Causa típica (ejecución 508599)

El nodo **Decidir temperatura** lanzaba `Night heating self-test failed`: el caso de prueba de las **07:30** (`m=450`) esperaba 0 comandos pero, con la ventana 18:00–08:00, debe permitir encendido → **2 comandos**. Corregido en n8n (`450,0` → `450,2`).

### Workflow de alertas

- ID error workflow: `EltiT3iY5IoJY3yU` — **SmartLife Buhardilla — alertas error**
- Enlazado en `settings.errorWorkflow` del workflow principal.
- Añade credencial **Telegram** en n8n y variable de entorno `TELEGRAM_CHAT_ID` (o cambia el nodo por WhatsApp/2Chat).

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