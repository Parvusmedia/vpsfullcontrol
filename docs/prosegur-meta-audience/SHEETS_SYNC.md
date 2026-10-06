# Prosegur — sincronización desde Google Sheets

Workflow central: **`prosegur-phone-register`**  
Editor: https://pmedia.app.n8n.cloud/workflow/IlydJZl4v1fomiyY

## Objetivo

Sin nodos extra en cada flujo proveedor: el workflow central lee la **fuente de verdad** (Google Sheets), deduplica teléfonos España y escribe **solo números nuevos** en la data table `prosegur_phone_events` (id `ZI6qiUvYUVzuCJM6`).

## Google Sheet

| | |
|--|--|
| Documento | `1Fna1muuArgG_eaehXPAyl9AnRm6VOjcQc6JyO05-y_4` |
| Pestaña **Prosegur** | `gid=0` |
| Pestaña **leadsconhorario_soportesexternos** | `gid=412852702` |

Columnas usadas: **`Fecha`**, **`telefono`**, **`source`** (si falta `source`, se usa el nombre de la pestaña).

## Ventana temporal

- **Últimas 24 horas** respecto a la hora de ejecución (timezone del workflow: `Europe/Madrid`).
- `Fecha` admite ISO, serial de Google Sheets o `dd/mm/yyyy`.

## Volumen de lectura (Google Sheets)

**No** se lee el sheet entero en cada ciclo (~48k + ~13k filas): eso ralentiza n8n y consume cuota de la API de Google.

El nodo **Read** de Google Sheets **no admite** filtro tipo “fecha ≥ ayer” (solo igualdad exacta por columna). Por eso:

1. **`Prep read range`**: calcula `firstDataRow` = última fila conocida − **cola** (por defecto **4000** filas; variable opcional `$vars.PROSEGUR_SHEETS_TAIL_ROWS`).
2. **`Update high water`**: guarda el `row_number` máximo visto para acotar mejor la cola en la siguiente ejecución.
3. **`Filter 24h rows`**: dentro de esa cola, solo pasan filas con `Fecha` en las últimas 24 h.

Tras la primera ejecución, cada pestaña debería leer del orden de **miles** de filas, no decenas de miles.

Alternativas más eficientes (Apps Script, pestaña QUERY): [SHEETS_INGEST_OPTIONS.md](./SHEETS_INGEST_OPTIONS.md).

## Cadena del workflow

```text
Schedule (cada 15 min) / Manual Trigger
  → Read Prosegur + Read leadsconhorario (paralelo)
  → Merge → Filter 24h rows
  → Register (staticData: phones + processedSheetRows)
  → IF solo is_duplicate=false
  → Insert Data Table (duplicate_tag=new)
```

### Dedup

1. **`processedSheetRows`**: evita reprocesar la misma fila del sheet en cada ciclo (clave `pestaña:row:Fecha:telefono`).
2. **`phones`**: registro maestro; si el teléfono ya existía → **no** se inserta en la data table (pero la fila del sheet queda marcada como procesada).

Los flujos proveedor pueden usar **Get row** en la data table: solo aparecen teléfonos **nuevos** (primera aparición en el histórico de sheets).

### Latencia y dedup en proveedor

- Tras un lead en sheet, puede tardar **hasta ~15 min** (o hasta un **Test workflow** manual del central) hasta que el teléfono aparezca en la data table.
- Un **duplicado** (mismo teléfono ya registrado) **no** genera fila nueva en la table, pero la **primera** fila sigue ahí → **Get row** por `phone_digits` sigue detectando duplicados **después** de que el primer lead se sincronizó.

## Despliegue

```bash
scripts/n8n update --workflow-id IlydJZl4v1fomiyY --file n8n/workflows/prosegur-phone-register.json
```

Tras importar, confirmar credencial **Pmedia Dvelopment Google** en los nodos Read.

## Prueba

1. **Test workflow** (Manual Trigger).
2. Revisar ejecución: **Filter 24h rows** → **Register** → **Insert Data Table**.
3. Comprobar filas nuevas en Data table.

## Webhook legacy

El webhook `prosegur-phone-register` se **eliminó** de este workflow. Si algún flujo aún lo llamaba, dejar de usarlo o restaurar un workflow aparte solo-webhook.
