# Cómo ingestar leads del Sheet sin leer decenas de miles de filas

Comparativa para **`1Fna1muuArgG_eaehXPAyl9AnRm6VOjcQc6JyO05-y_4`** (pestañas **Prosegur**, **leadsconhorario_soportesexternos**).

## Opciones (de más a menos eficiente)

| Enfoque | Filas tocadas / hora | Complejidad | Latencia |
|--------|----------------------|-------------|----------|
| **A. Apps Script al append** (trigger al insertar fila) | ~1 por lead | Media | Segundos |
| **B. Apps Script + cursor** (solo filas nuevas desde última fila vista) | Decenas–cientos | Media | 1 h (o el cron que elijas) |
| **C. Apps Script + cola 24 h** (lee solo últimas N filas en script, filtra `Fecha`) | Cientos–miles | Baja | 1 h |
| **D. Pestaña QUERY `_24h`** (Sheet filtra; n8n lee solo esa pestaña) | Solo matches 24 h | Baja en n8n | 15 min (n8n schedule) |
| **E. n8n “cola” 4000 filas** (actual) | ~4000 × 2 pestañas | Ya desplegado | 15 min |

**Recomendación Prosegur:** **B** o **A**. El script corre **dentro** de Google: no cuenta contra la cuota OAuth de n8n y puedes leer `getLastRow()` y solo un rango pequeño.

---

## A / B — Apps Script → webhook n8n (recomendado)

1. **Script** (en el propio spreadsheet): trigger **time-driven** cada hora **o** `onChange`/formulario según cómo entren los leads.
2. Por pestaña:
   - Guardar **`lastRowProcessed`** en `PropertiesService` (cursor).
   - Leer solo filas `(lastRowProcessed + 1) … getLastRow()`.
   - Opcional: descartar filas con `Fecha` &lt; now − 24 h.
3. **POST** JSON a n8n (`/webhook/prosegur-sheet-ingest`) con header secreto y array de `{ telefono, source, sheet_tab, row_number, fecha }`.
4. **n8n**: webhook → normalizar → dedup (`staticData`) → insert data table (misma lógica que hoy, **sin** nodos Google Sheets Read).

Ventajas:

- n8n deja de tirar de 48k filas.
- Dedup y data table siguen centralizados en un solo workflow.
- Puedes bajar el schedule n8n o **desactivar** el workflow solo-lectura-Sheet cuando el script esté estable.

Script de ejemplo en el repo: [`google-apps-script/prosegur-sheet-scan.gs`](../../google-apps-script/prosegur-sheet-scan.gs) (`prosegurDailySheetPush`: cola **500** filas, ventana **24 h**, dedup, webhook `prosegur-phone-register`).

---

## D — Pestaña auxiliar QUERY (sin Apps Script)

Crear pestaña p. ej. **`prosegur_ultimas_24h`** con fórmula que una ambas fuentes o duplicar QUERY por pestaña. n8n **Read** solo esa pestaña (~filas del día).

Inconvenientes: mantener índices de columna (`Fecha` = columna D en **Prosegur**), límites de `QUERY`, y carga recalcular el Sheet en cada edición.

---

## E — Lo que tienes ahora (cola en n8n)

Válido como paso intermedio. Variable `$vars.PROSEGUR_SHEETS_TAIL_ROWS` (default 4000) si sube el volumen diario.

---

## Migración sugerida

1. Añadir workflow **`prosegur-sheet-ingest-webhook`** (batch) o reactivar rama webhook en el central.
2. Desplegar Apps Script + trigger horario; probar con `dryRun` en logs.
3. Comparar conteos con el workflow actual 1–2 días.
4. Desactivar schedule **Read Prosegur / Read leadsconhorario** en `IlydJZl4v1fomiyY`.
