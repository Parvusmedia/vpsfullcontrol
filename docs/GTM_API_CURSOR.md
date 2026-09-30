# Google Tag Manager API (para Cursor / automatización)

Objetivo: que un agente (Cursor Cloud o SSH en `parvus-vps`) pueda **leer y editar** el contenedor web de parvusmedia.com vía API, sin usar la UI de GTM.

Contenedor público: **GTM-T9JWZZ3Q** (los IDs numéricos de cuenta/contenedor se obtienen con el script de verificación).

## 1. Proyecto en Google Cloud

1. Entra en [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto nuevo (p. ej. `parvus-gtm`) o elige uno existente de Parvus Media.
3. Anota el **Project ID** (no confundir con el nombre visible).

## 2. Activar la API

1. **APIs y servicios** → **Biblioteca**.
2. Busca **Tag Manager API**.
3. Pulsa **Habilitar**.

(O desde CLI con `gcloud`: `gcloud services enable tagmanager.googleapis.com --project=TU_PROJECT_ID`)

## 3. Cuenta de servicio (recomendado para agentes)

Las cuentas de servicio encajan con automatización; no uses tu usuario personal como “clave” en el servidor.

1. **IAM y administración** → **Cuentas de servicio** → **Crear cuenta de servicio**.
2. Nombre sugerido: `cursor-gtm-parvusmedia`.
3. Rol en GCP (opcional para GTM puro): ninguno obligatorio en el proyecto; los permisos reales se dan **dentro de GTM** (paso 4).
4. **Claves** → **Agregar clave** → **JSON** → descarga el archivo (una sola vez).
5. **No subas ese JSON a GitHub.** Guárdalo solo en el VPS o en secretos de Cursor.

## 4. Dar acceso en Tag Manager (imprescindible)

La API **no funciona** solo con la clave JSON: el email de la cuenta de servicio debe ser usuario del contenedor.

1. [tagmanager.google.com](https://tagmanager.google.com/) → contenedor **GTM-T9JWZZ3Q**.
2. **Administración** (engranaje) → **Administración de usuarios** (a nivel de **cuenta** o **contenedor**).
3. **Añadir usuarios** → pega el email de la cuenta de servicio  
   (`cursor-gtm-parvusmedia@TU_PROJECT_ID.iam.gserviceaccount.com`).
4. Permiso recomendado para el agente: **Editar** (crear tags/variables/triggers).  
   Usa **Publicar** solo si quieres que el agente también **publique** versiones en producción.

## 5. Guardar credenciales en el VPS (Parvus)

Patrón alineado con otros secretos (`/opt/apps/private/cde/`):

```bash
# En parvus-vps (como cursorbot o tú por SSH)
sudo mkdir -p /opt/apps/private/parvusmedia-web
sudo chown cursorbot:cursorbot /opt/apps/private/parvusmedia-web
chmod 700 /opt/apps/private/parvusmedia-web

# Sube el JSON (desde tu máquina, ejemplo)
scp gtm-service-account.json parvus-vps:/opt/apps/private/parvusmedia-web/gtm-service-account.json
ssh parvus-vps 'chmod 600 /opt/apps/private/parvusmedia-web/gtm-service-account.json'
```

Archivo de entorno (sin secretos en git), plantilla en `parvusmedia-web/deploy/gtm-api.env.example`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/opt/apps/private/parvusmedia-web/gtm-service-account.json
# Opcional: rellenar tras el primer `scripts/gtm accounts`
GTM_ACCOUNT_ID=
GTM_CONTAINER_ID=
GTM_WORKSPACE_ID=
```

Copia en el VPS:

```bash
cp gtm-api.env.example /opt/apps/private/parvusmedia-web/gtm-api.env
chmod 600 /opt/apps/private/parvusmedia-web/gtm-api.env
```

## 6. Cursor Cloud Agent (opcional)

Si quieres que el agente en la nube use la API **sin** depender solo de SSH:

1. En el dashboard de Cursor → **Cloud Agent** / **Secrets** del entorno (o variables del agente).
2. No pegues el JSON entero en un chat.
3. Opciones habituales:
   - Variable `GOOGLE_APPLICATION_CREDENTIALS` apuntando a ruta si el JSON se instala en el snapshot del entorno (menos habitual), o
   - Secret multilínea con el contenido del JSON y un script de arranque que lo escriba en `/tmp/gtm-sa.json` (solo en el pod del agente).

Lo más simple para Parvus hoy: **dejar el JSON solo en `parvus-vps`** y que el agente use `ssh parvus-vps` + `scripts/gtm` (ya tiene acceso `cursorbot`).

## 7. Verificar

Desde el repo (con SSH a `parvus-vps` o con el JSON en local):

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/ruta/al/gtm-service-account.json
pip install -q -r scripts/requirements-gtm.txt
scripts/gtm accounts
scripts/gtm containers --account-id NUMERIC_ACCOUNT_ID
```

Si `accounts` devuelve tu cuenta y `containers` lista **GTM-T9JWZZ3Q**, la configuración está bien.

## 8. Qué puede hacer el agente con la API

- Listar cuentas, contenedores, workspaces.
- Crear/editar **variables**, **activadores (triggers)** y **etiquetas** en el workspace por defecto.
- Crear una **versión** del contenedor y **publicarla** (si el usuario de la cuenta de servicio tiene permiso Publicar).

La API **no sustituye** pruebas en **Vista previa** de GTM; conviene seguir validando eventos en el sitio.

## 9. Seguridad

- Rota o revoca la clave JSON si se filtra.
- Permiso mínimo en GTM: **Editar** hasta que confíes en flujos automáticos de publicación.
- No envíes emails u otros PII en parámetros de GA4 desde tags creadas por API.

## Referencias

- [Tag Manager API v2](https://developers.google.com/tag-platform/tag-manager/api/v2)
- [Autenticación](https://developers.google.com/tag-platform/tag-manager/api/v2/authorization)
