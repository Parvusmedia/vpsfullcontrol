# Prosegur — workflow central `prosegur-phone-register` (fase 1)

Recibe teléfono + proveedor, normaliza (España), consulta el registro y **reserva** el número o devuelve duplicado. **No llama a Meta** (fase 2: `prosegur-meta-audience-push`).

## Persistencia (v1 en n8n Cloud)

El workflow desplegado usa **`$getWorkflowStaticData('global')`** (nodos **Register**): mapa `phones` + lista `duplicateEvents`. No requiere Data Store/Data Table en la instancia (el tipo `dataStore` no está disponible en vuestro cloud).

Más adelante se puede migrar a **Data tables** (`n8n-nodes-base.dataTable`) sin cambiar el contrato HTTP.

## Data Stores / Data tables (referencia futura)

### 1. `prosegur_meta_phones`

| Campo | Tipo | Notas |
|-------|------|--------|
| `phone_digits` | string | **Clave única**, ej. `34612345678` |
| `phone_hash` | string | SHA256 del `phone_digits` (Meta) |
| `first_source` | string | Primer proveedor/flujo |
| `first_seen_at` | string | ISO-8601 |
| `claimed_at` | string | ISO-8601 (misma reserva) |
| `meta_synced_at` | string | Vacío hasta fase Meta |

### 2. `prosegur_meta_duplicate_events`

| Campo | Tipo | Notas |
|-------|------|--------|
| `event_key` | string | **Clave única**, ej. `dup_34612345678_2026-03-01T12:00:00.000Z` |
| `phone_digits` | string | |
| `received_at` | string | ISO-8601 |
| `source` | string | Proveedor que reintentó |
| `first_source` | string | Del registro maestro |
| `first_seen_at` | string | Del registro maestro |
| `action` | string | `duplicate_not_processed` |

## Secreto del webhook (n8n Variables)

En n8n Cloud **no** uses `$env` en Code (bloqueado). El workflow lee:

**`$vars.PROSEGUR_PHONE_REGISTER_SECRET`**

Crear o editar en **Settings → Variables** (clave `PROSEGUR_PHONE_REGISTER_SECRET`). El mismo valor va en el header `X-Prosegur-Register-Secret` de los flujos proveedor.

Tras rotar el secreto: actualizar la variable en n8n y los nodos HTTP de los flujos hijos.

## Importar workflow

**Credenciales locales (no commitear):** archivo `private/n8n.env` con `N8N_URL` y `N8N_REST_API_KEY`. `scripts/n8n` lo carga automáticamente si existe.

**Opción A — REST (agente / CI):** con `N8N_REST_API_KEY` (JWT public-api o `n8n_api_...`):

```bash
scripts/n8n import --file n8n/workflows/prosegur-phone-register.json --activate
```

Devuelve `editor_url` y `workflow_id`. El MCP (`N8N_MCP_TOKEN` / JWT) solo permite buscar y ejecutar workflows, no crearlos.

**Opción B — UI:** **Workflows → Import from File** → [`n8n/workflows/prosegur-phone-register.json`](../../n8n/workflows/prosegur-phone-register.json).

Pasos comunes tras importar:
2. En cada nodo **Data store**, elegir el store correspondiente (`prosegur_meta_phones` / `prosegur_meta_duplicate_events`). Si tras importar la operación no coincide con tu versión de n8n, ajusta: **Get** en `Get phone`, **Create/Set** en `Claim phone` y `Log duplicate`.
3. En el nodo **Get phone**, activar **Always Output Data** si no viene ya marcado (así el flujo sigue cuando el teléfono no existe).
4. Configurar `PROSEGUR_PHONE_REGISTER_SECRET` en el proyecto.
4. Activar workflow y copiar la **Production URL** del Webhook.

## Contrato HTTP

**POST** `…/webhook/prosegur-phone-register` (path según n8n)

Headers:

- `Content-Type: application/json`
- `X-Prosegur-Register-Secret: <secreto>`

Body:

```json
{
  "phone": "612 345 678",
  "source": "proveedor_ejemplo"
}
```

### Respuestas

| HTTP | `status` | Significado |
|------|----------|-------------|
| 200 | `claimed` | Primera vez; fila creada en `prosegur_meta_phones` |
| 400 | `duplicate_not_processed` | Ya existía; evento en `prosegur_meta_duplicate_events` |
| 422 | `invalid_phone` | No pasa validación España |
| 401 | `unauthorized` | Secreto incorrecto |

Ejemplo 200:

```json
{
  "status": "claimed",
  "phone_digits": "34612345678",
  "source": "proveedor_ejemplo",
  "claimed_at": "2026-03-01T11:00:00.000Z"
}
```

Ejemplo 400:

```json
{
  "status": "duplicate_not_processed",
  "phone_digits": "34612345678",
  "source": "proveedor_B",
  "first_source": "proveedor_A",
  "first_seen_at": "2026-03-01T10:00:00.000Z",
  "message": "duplicated phone, not processed"
}
```

## Fase 2 — flujos proveedor (lo haréis vosotros)

Antes de `Respond to Webhook` al proveedor:

1. **HTTP Request** (sync) al workflow central con `phone` + `source`.
2. Si respuesta **200** y `status === claimed` → **200** al proveedor y seguir procesamiento; luego llamar a push Meta (cuando exista).
3. Si respuesta **400** → **400** al proveedor con `duplicated phone, not processed` (no procesar lead).

## Prueba con curl

```bash
curl -sS -X POST "$PROSEGUR_REGISTER_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Prosegur-Register-Secret: $PROSEGUR_PHONE_REGISTER_SECRET" \
  -d '{"phone":"612345678","source":"curl_test"}'
```

Repetir el mismo comando: debe devolver **400** y `duplicate_not_processed`.

## Meta (referencia, fase 2)

- Audiencia: `52551337752304` (MPA_Lead_Exclusion 3rdparty)
- BM: `149543758710373`
