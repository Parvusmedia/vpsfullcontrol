# Blueprint n8n — Holded facturas → Sheets (CDE / Havas)

## Webhook Holded (ya creado)

| Campo | Valor |
|--------|--------|
| URL n8n (producción) | `https://pmedia.app.n8n.cloud/webhook/holded-invoices-cde` |
| Eventos | `invoice.create`, `invoice.approve` |
| Webhook id Holded | `6aba37d34dda73b56206c392` |
| Secret | `HOLDED_WEBHOOK_SECRET` en `/opt/apps/private/cde/holded.env` (parvus-vps) |

Verificación firma: header `x-holded-webhook-signature` (HMAC-SHA256 del body raw, prefijo `sha256=`).

## Filtro

Solo procesar si `contact_id` (o `contact.id` en payload) = `6023ce4a0a356d6caf64b163`.

## Google Sheet

- ID: `1IYiaHazczGDWsMIQosu9Ggpws1Lv2JkicCkshnt5-D0`
- Pestaña `Facturas`: clave `invoice_id` (Append or Update)
- Pestaña `Routing`: lectura en fase email (approve)

Columnas: ver [holded-facturas-havas-sheet.md](../holded-facturas-havas-sheet.md).

## Flujo sugerido (workflow único)

1. **Webhook** POST (raw body para firma).
2. **Code** — validar firma con secret del env/credencial n8n.
3. **Switch** — `x-holded-webhook-event`.
4. **IF** — contacto objetivo.
5. **HTTP** (opcional) — `GET /api/v2/invoices/{id}` si faltan líneas/tags.
6. **Google Sheets** — `invoice.create` → upsert fila, `estado=borrador`.
7. **Google Sheets** — `invoice.approve` → upsert, `estado=aprobada`, `email_estado=pendiente`.
8. *(Fase 2)* PDF + SMTP + routing.

## Credenciales n8n

- Holded API: Bearer desde credencial o env (mismo PAT que VPS).
- Webhook secret: credencial separada (no loguear en ejecuciones).

## Workflow en n8n Cloud (desplegado)

| Campo | Valor |
|--------|--------|
| Nombre | `holded-facturas-havas-cde` |
| Id | `jvDmNuv4PqjFGZ7C` |
| Activo | sí |
| Webhook path | `holded-invoices-cde` |

Nodos: Webhook (raw body) → firma HMAC → contactos Havas (`6023…` y `653f…`) → evento → Sheet `Facturas` → en **approve**: leer `Routing`, match **tag**, PDF Holded, email SMTP, actualizar `email_estado`.

**OAuth Google Sheets:** si el deploy por API pierde credenciales, en el editor n8n reasigna **Google Sheets account** en los 4 nodos Sheets (limitación API). SMTP: **Hola@ SMTP N8N** en `Email factura`.

### Redesplegar / actualizar

En un host con `holded.env` y API key n8n (p. ej. tras `git pull`):

```bash
export N8N_BASE_URL=https://pmedia.app.n8n.cloud
export N8N_API_KEY=n8n_api_...   # o leer desde deployment.local.env en VPS
python3 scripts/deploy-holded-invoices-n8n.py
```

El script embebe `HOLDED_WEBHOOK_SECRET` solo en el nodo Code de n8n (no en git).

### Prueba manual

Fila de prueba `test_invoice_n8n_001` / `TEST-N8N-001` en la hoja (puedes borrarla).
