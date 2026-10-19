# Meta Ads desde Cursor (acceso partner Parvus)

Cliente BM: `461966487998679` · Ad account: `476956206434765` · Partner Parvus BM: `688106874654286`.

## 1. Token (sin admin en el BM del cliente)

Como agencia con activos compartidos en tu BM de Parvus:

1. [Meta Business Settings](https://business.facebook.com/settings) → **Parvus Media** (`688106874654286`).
2. **Usuarios → Usuarios del sistema** → crear o reutilizar uno (p. ej. `cursor-meta`).
3. **Asignar activos** del cliente ya compartidos contigo:
   - Cuenta publicitaria `476956206434765`
   - Páginas que uses para lead forms (cuando las tengas).
4. **Generar token** del system user con permisos mínimos:
   - `ads_management`
   - `business_management`
   - `pages_manage_ads`
   - `pages_read_engagement`
   - `leads_retrieval` (si luego lees leads)
5. Usa una **app de Meta** de Parvus (Developers) vinculada al system user.

Guarda el token fuera de git (ver `deploy/meta.env.example`).

## 2. Alcance solo Digitanimal

En el Cloud Agent de este cliente, define:

```bash
META_SCOPE=digitanimal
META_CLIENT_BUSINESS_ID=<digitanimal_bm_id>
META_AD_ACCOUNT_ID=<digitanimal_ad_account_id>
```

El CLI rechaza otras ad accounts y `page_id` fuera de `deploy/meta_digitanimal_allowlist.json`. Comprueba con `scripts/meta scope` y `scripts/meta list-pages` (solo muestra páginas Digitanimal).

## 3. Variables en el entorno del Cloud Agent

En el environment de Cursor (secrets), o en un fichero que solo exista en el pod/VPS:

```bash
export META_ENV_FILE=/ruta/private/cliente/meta.env
# o exportar directamente:
export META_ACCESS_TOKEN='...'
export META_AD_ACCOUNT_ID=476956206434765
export META_CLIENT_BUSINESS_ID=461966487998679
export META_PARTNER_BUSINESS_ID=688106874654286
export META_PRIVACY_POLICY_URL='https://dominio-cliente.com/privacidad'
```

## 3. Comandos

```bash
chmod +x scripts/meta
scripts/meta status
scripts/meta list-pages

# Vista previa (no llama a Meta)
scripts/meta create-campaign --name "Cliente - Leads Q4" --dry-run
scripts/meta create-campaign --name "Cliente - Leads Q4"

scripts/meta create-adset --campaign-id <ID> --page-id <PAGE_ID> --name "Ad set ES" --dry-run
scripts/meta create-adset --campaign-id <ID> --page-id <PAGE_ID> --name "Ad set ES"

scripts/meta create-form --page-id <PAGE_ID> --name "Formulario landing" --dry-run
scripts/meta create-form --page-id <PAGE_ID> --name "Formulario landing" --template deploy/meta_lead_form.example.json
```

Convenciones:

- Campañas y ad sets se crean en **`PAUSED`** (equivalente operativo a borrador).
- **Formularios de leads:** la Graph API **no respeta** `status=DRAFT` en la práctica: un form completo queda **`ACTIVE`** y suele mostrar **Sharing: Restricted**, sin pasar por la pestaña *Draft forms* ni ser editable como un borrador creado en la UI.  
  **Flujo recomendado:** en Ads Manager → **Draft forms** → *Duplicate* del form origen → nombre/URL → publicar cuando esté listo.  
  Desde Cursor: `scripts/meta duplicate-form ... --prepare-only` genera el spec (nombre, preguntas, follow-up) para aplicarlo al duplicar en la UI.  
  Solo usar `duplicate-form` sin `--prepare-only` si aceptas un form **ACTIVE** vía API.
- Los nombres llevan prefijo `[CURSOR-DRAFT]` salvo `--exact-name`.

## 4. App Review

En modo desarrollo de la app, solo funcionan usuarios/system users añadidos a la app. Para automatización estable del cliente, conviene pasar revisión de Meta en los permisos usados.

## 5. Siguiente paso en chat

Cuando tengas el **page_id** y el token cargado en el environment:

1. `scripts/meta status` debe mostrar `ad_account` OK.
2. Pedir en Cursor: *“Crea formulario DRAFT en la página X”* o *“Campaña + ad set pausados para leads”*.
