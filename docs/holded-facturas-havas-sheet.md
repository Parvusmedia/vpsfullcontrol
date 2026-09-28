# Google Sheet — facturas Holded (HavasMedia)

Spreadsheet: `1IYiaHazczGDWsMIQosu9Ggpws1Lv2JkicCkshnt5-D0`  
[Abrir hoja](https://docs.google.com/spreadsheets/d/1IYiaHazczGDWsMIQosu9Ggpws1Lv2JkicCkshnt5-D0/edit)

Cliente Holded (filtro n8n): `6023ce4a0a356d6caf64b163`

## Pestañas y cabeceras (fila 1)

### `Facturas`

Pega en **A1** (una fila, tabuladores entre columnas):

```
invoice_id	numero	fecha	vencimiento	estado	total	moneda	tags_factura	lineas_resumen	contact_id	creada_en	aprobada_en	email_estado	destinatarios	ultimo_error
```

### `Routing`

Pega en **A1**:

```
prioridad	tipo	valor	emails	asunto	activo
```

Ejemplo de regla (fila 2):

```
10	tag	Hosting	destino@ejemplo.com	Factura {{numero}}	SI
```

## Si la hoja está en solo lectura

Comparte el documento como **Editor** con la cuenta que usará n8n (OAuth) o con `forwardespana@gmail.com` si automatizas vía Zapier. Luego renombra `Hoja 1` → `Facturas` y añade la pestaña `Routing`.

## Archivos de importación

- [`holded-facturas-Facturas-headers.tsv`](holded-facturas-Facturas-headers.tsv)
- [`holded-facturas-Routing-headers.tsv`](holded-facturas-Routing-headers.tsv)

En Google Sheets: **Archivo → Importar** → subir TSV → *Insertar filas* en la pestaña correspondiente.
