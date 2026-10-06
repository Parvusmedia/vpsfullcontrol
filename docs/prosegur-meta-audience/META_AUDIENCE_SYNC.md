# Prosegur — sync diario a Meta Custom Audience

Workflow: **`prosegur-meta-audience-sync`**  
Audiencia: **MPA_Lead_Exclusion (3rdparty)** — ID `52551337752304`  
Business Manager: `149543758710373`

## Qué hace

1. Lee la data table **`prosegur_phone_events`** (`ZI6qiUvYUVzuCJM6`) filas con `duplicate_tag=new`.
2. Excluye teléfonos ya enviados (`meta_synced_at` en la fila o registro en `staticData.syncedPhones` del workflow).
3. Sube hashes **SHA256** de `phone_digits` (columna `phone_hash`) a Meta vía  
   `POST /v23.0/{audience-id}/users` (lotes de hasta 5000).
4. Marca `meta_synced_at` en la data table y en memoria del workflow.

## Variables n8n (Settings → Variables)

| Variable | Valor |
|----------|--------|
| `meta_systemusertoken_Adsmanager_PmediaES_Agent` | System user Ads Manager Pmedia ES (ya existente en n8n Variables) |
| `PROSEGUR_META_CUSTOM_AUDIENCE_ID` | Opcional; por defecto `52551337752304` |

No commitear el token. Rotar en Meta si se filtra.

## Data table — columna nueva

Añadir en **prosegur_phone_events**:

| Columna | Tipo |
|---------|------|
| `meta_synced_at` | string (ISO-8601) |

Si falta, el sync sigue funcionando (dedup en `staticData`); el nodo **Update meta_synced_at** fallará en silencio (`continueOnFail`).

## Despliegue

```bash
scripts/n8n import --file n8n/workflows/prosegur-meta-audience-sync.json --activate
```

## Horario

- **Cron:** `0 5 * * *` (05:00 Europe/Madrid), después del push diario del Sheet (~01:00–02:00).
- **Prueba:** Manual Trigger en el editor.

## Alertas si falla

El workflow usa el **Error Workflow** compartido **`Workflow con Error Alerta X Email`** (`e1XnUCiGOtnaoJVB`): mismo patrón que otros flujos Prosegur/Meta. Si una ejecución termina en error (p. ej. nodo **Meta add users**), n8n dispara ese subflujo y envía email a las direcciones configuradas allí (`etichauer@gmail.com`, `emiliano@parvusmedia.com`).

Para cambiar destinatarios o el asunto, edita el workflow de alertas en n8n, no el sync de Prosegur.

## Comprobar en Meta

Ads Manager → Audiencias → `MPA_Lead_Exclusion (3rdparty)` → tamaño de la audiencia (puede tardar en actualizarse).

## Errores habituales

| Síntoma | Causa |
|---------|--------|
| `Invalid OAuth access token` | Variable `meta_systemusertoken_Adsmanager_PmediaES_Agent` vacía o caducada |
| `Permissions error` | Token sin acceso al BM / audiencia |
| `num_invalid_entries` > 0 | Hash o formato de teléfono no aceptado por Meta (revisar normalización España) |
