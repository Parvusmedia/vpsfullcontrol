# Data table `prosegur_phone_events`

Registro visible de **teléfonos nuevos** del webhook **prosegur-phone-register**: **una fila por `phone_digits`**. Los reintentos (duplicados) **no** insertan fila; el webhook responde 200 con `duplicate_tag=duplicate`.

## Columnas

| Columna | Tipo | Valores |
|---------|------|---------|
| `phone_digits` | string | E.164 sin `+`, ej. `34612345678` |
| `duplicate_tag` | string | `new` \| `duplicate` |
| `is_duplicate` | string | `no` \| `yes` |
| `source` | string | Proveedor de esta llamada |
| `first_source` | string | Primer proveedor que registró el teléfono |
| `received_at` | string | ISO-8601 de esta llamada |
| `first_seen_at` | string | ISO-8601 del primer registro |
| `phone_hash` | string | SHA256 de `phone_digits` |
| `meta_synced_at` | string | ISO-8601 cuando se subió a Meta (vacío = pendiente). Ver [META_AUDIENCE_SYNC.md](./META_AUDIENCE_SYNC.md). |

La deduplicación operativa sigue en **`$getWorkflowStaticData('global')`** (nodo **Register**). La data table es copia de auditoría; no sustituye el registro maestro hasta una migración futura.

## Crear la tabla (obligatorio una vez)

En **pmedia.app.n8n.cloud** (oct-2025):

- El nodo **Data table → Table → Create** falla con `Could not get parameter` (la instancia aún no expone CRUD de tablas en el nodo).
- **`POST /api/v1/data-tables`** responde **404** (API pública de data tables no habilitada en cloud).

**Opción recomendada — UI**

1. Abrir el proyecto en n8n → pestaña **Data tables** (Overview).
2. **Create data table** → nombre exacto: **`prosegur_phone_events`**
3. Añadir las columnas de la tabla anterior (todas **string**).

**Opción B — workflow setup (cuando n8n actualice el nodo)**

1. Importar [`n8n/workflows/prosegur-setup-phone-events-table.json`](../../n8n/workflows/prosegur-setup-phone-events-table.json)
2. En el editor, **Test workflow** (Manual Trigger → Create Data Table).

Editor del setup en cloud: `https://pmedia.app.n8n.cloud/workflow/cxoCxud0C04seDFw`

## Workflow central

Archivo: [`n8n/workflows/prosegur-phone-register.json`](../../n8n/workflows/prosegur-phone-register.json)

Cadena de auditoría:

`Register` (staticData + lookup en data table) → **Only new phone** → si es nuevo: **Prepare audit row** → **Insert Data Table** → **Respond 200**. Si es duplicado: **Respond 200 duplicate** (sin insert).

Si la tabla no existe, el webhook **sigue respondiendo 200**; el nodo Insert registra error en la ejecución (`Could not find the data table`).

## Contrato HTTP (batch — Apps Script diario)

**POST** `…/webhook/prosegur-phone-register`

```json
{
  "batch_id": "gas-2026-10-06T08:00:00",
  "leads": [
    {
      "phone": "612345678",
      "source": "Prosegur",
      "row_number": 13003,
      "sheet_tab": "Prosegur"
    }
  ]
}
```

Respuesta **200**:

```json
{
  "ok": true,
  "batch_id": "…",
  "stats": { "input": 10, "new": 8, "duplicate": 1, "invalid": 1, "inserted": 8 },
  "results": [
    { "index": 0, "status": "new", "phone_digits": "34612345678", "duplicate_tag": "new" },
    { "index": 1, "status": "duplicate", "phone_digits": "34699999999", "message": "duplicate_not_processed" }
  ]
}
```

Sigue admitiendo un lead suelto `{ "phone", "source" }` (compatibilidad).

## Comprobar

Tras crear la tabla, dos POST al webhook con el mismo teléfono deben generar:

1. **Una** fila con `duplicate_tag=new`, `is_duplicate=no`
2. Segunda llamada: **sin** fila nueva; JSON con `duplicate_tag=duplicate`, `message=duplicate_not_processed`

Ver filas en **Data tables → prosegur_phone_events** o en el historial de ejecuciones del nodo **Insert Data Table**.
