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

### Regla activa: `telefonicaseguros` (fila 2)

| prioridad | tipo | valor | emails |
|-----------|------|-------|--------|
| 10 | tag | telefonicaseguros | ana.lopez@havasmn.com; carolina.munoz-manas@havasmn.com; luisa.lopez@havasmn.com; rocio.teijeira@havasmn.com |

Asunto: `Factura {{numero}} - telefonicaseguros`

Factura ejemplo: `6ab4a344919f511bf3067da4` (`FCTRA-2026-180`), contacto Holded `653f9fdfa0105e3d910cbbe7` (segunda ficha Havas; también se acepta `6023ce4a0a356d6caf64b163`).

## Estado (2026-09-28)

Pestañas **Facturas** y **Routing** creadas con cabeceras en fila 1 (documento *Facturas HavasMedia*).

Si rehaces la hoja desde cero, comparte como **Editor** la cuenta Google de n8n y aplica las cabeceras de abajo o importa los TSV.

## Archivos de importación

- [`holded-facturas-Facturas-headers.tsv`](holded-facturas-Facturas-headers.tsv)
- [`holded-facturas-Routing-headers.tsv`](holded-facturas-Routing-headers.tsv)

En Google Sheets: **Archivo → Importar** → subir TSV → *Insertar filas* en la pestaña correspondiente.
