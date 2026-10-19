# Digitanimal — Meta Lead Ads: slugs de campos y nomenclatura

**Guía para quien crea formularios en Meta:** [digitanimal-guia-formularios-meta.md](./digitanimal-guia-formularios-meta.md).

Carpeta Make: **Digitanimal** (`folderId` **404390**, team **38243**).

Escenarios:

| País | Escenario | ID | Hoja Google |
|------|-----------|-----|-------------|
| ES | Digitanimal_Spain_Meta-LeadAds | 7950608 | `meta_DigitanimalES` |
| FR | Digitanimal_FR_Meta-LeadAds | 7951407 | `meta_DigitanimalFR` |
| IT | Digitanimal_IT_Meta-LeadAds | 7952998 | `meta_DigitanimalIT` |

## Cómo Meta nombra los campos en Make

Make expone los datos del formulario en `1.data.<slug>`. El **slug lo genera Meta** a partir del texto de la pregunta (minúsculas, espacios → `_`, signos de puntuación conservados). No coincide con la etiqueta visible del anuncio.

Si usas el **tipo de pregunta predefinido** de Meta (Email, Phone number, Full name), el slug suele ser estable en inglés:

| Tipo Meta (Lead form) | Slug esperado en `1.data` |
|----------------------|---------------------------|
| Email | `email` |
| Phone number | `phone_number` |
| Full name | `full_name` |
| First name / Last name | `first_name` / `last_name` |

Si añades una pregunta **custom** con texto traducido (p. ej. «Número de teléfono»), Meta puede enviar **`número_de_teléfono`** en lugar de `phone_number`. Eso rompe escenarios que solo mapean `phone_number`.

## Inventario observado (blueprints + ejecuciones + samples)

La API `executions_get-detail` en este entorno **no devolvió I/O por módulo**; el catálogo se armó con **samples del blueprint**, **mappings** `1.data.*` y el caso de producción ES (`número_de_teléfono`).

### España — formulario test `1593102499206086` (sample)

| Slug Meta | Uso en Sheets / Make |
|-----------|----------------------|
| `email` | email |
| `full_name` | name |
| `phone_number` | teléfono (parse → `phone`) |
| `province` | province |
| `¿cuántos_animales_tienes?` | cant-animales (array → `[]`) |
| `¿qué_tipo_de_ganado_tienes?` | tipo_animal (array → `[]`) |

### España — formulario(s) producción (leads reales)

| Slug Meta | Notas |
|-----------|--------|
| `número_de_teléfono` | Mismo dato que teléfono; **no** `phone_number` |

### España — campaña **Leads_Báscula_ESP** (formulario `833329243095118`)

| Slug Meta | Uso en Noco / Sheets |
|-----------|----------------------|
| `nombre_y_apellidos` | **Nombre completo** (no viene `full_name`; Make/Noco deben mapear este slug primero) |
| `email` | email |
| `número_de_teléfono` / `phone_number` | teléfono |
| `province` | province |
| `¿cuántos_animales_tienes?` / variantes báscula | cant-animales |
| `¿qué_tipo_de_ganado_tienes?` / variantes | tipo_animal |

### Francia — formulario `1099884246301839` (sample + producción)

| Slug Meta | Uso en Sheets |
|-----------|----------------|
| `e-mail` | email |
| `prénom` | Si existe, **name / full_name** = `prénom` + (`nom_de_famille` o `full_name` si el apellido no viene separado) |
| `nom_de_famille` | Apellido cuando Meta lo envía aparte |
| `full_name` | En formularios FR a veces solo trae el **apellido**; no usar solo `ifempty(full_name; …)` si hay `prénom`. En Make, evitar `if(prénom != "")` sin comprobar existencia: en ES (sin `prénom`) puede devolver vacío y saltarse `full_name`. Usar `ifempty(trim(prénom & …); ifempty(full_name; …))`. |
| `numéro_de_téléphone` | parse → `phone`; columna province recibe copia del raw en mapping actual |
| `localisation_d’élevage` | *(sample; no mapeado a province en FR)* |
| `combien_d’animaux_avez-vous_?` | cant-animales |
| `quel_type_de_bétail_avez-vous_?` | tipo_animal |

### Italia

Formularios IT observados (oct 2026) usan slugs Meta predefinidos con **espacio** en el nombre:

| Slug Meta | Uso |
|-----------|-----|
| `full name` | nombre completo (no `full_name`) |
| `phone` | teléfono (no `phone_number`) |
| `correo_electrónico` / `email` | email |
| `provincia` | provincia |
| `quanti_animali_hai?` / `numero_di_animali` | cabezas (arrays) |
| `che_tipo_di_bestiame_hai?` / `tipo_di_animale` | tipo ganado (arrays) |

Escenario **7952998**: Noco coalesce multi-idioma + hoja **`meta_DigitanimalIT`** + parse teléfono `IT`.

## Columnas canónicas (destino Sheets)

Independientemente del slug Meta, la hoja usa siempre:

`date`, `source`, `campaign`, `adset`, `ad`, `campaignid`, `adsetid`, `adid`, `formid`, `leadid`, `name`, `email`, `phone`, `province`, `cant-animales`, `tipo_animal`, `custom4`–`custom6`.

## Reglas para **nuevos** formularios Meta

1. **Prioridad:** en el editor de formularios Meta, usar preguntas de tipo **Email**, **Phone number** y **Full name** (slugs `email`, `phone_number`, `full_name`) aunque la etiqueta visible esté en español/francés/italiano.
2. **Evitar** duplicar teléfono: no mezclar «Phone number» estándar y una pregunta custom «Número de teléfono» en el mismo formulario.
3. **Preguntas custom** (ganado, cabezas, provincia): aceptar que el slug será localizado; documentar el slug en esta tabla al crear el formulario (test lead + sample en Make).
4. **Make:** hasta que todos los forms usen slugs estándar, usar **coalesce** en filtros y parsers:

   ```text
   {{ifempty(1.data.phone_number; 1.data.`número_de_teléfono`)}}
   ```

   Análogo para email: `{{ifempty(1.data.email; 1.data.`e-mail`)}}` en FR.

5. **Checklist al publicar un form nuevo:**
   - Enviar 1 lead de prueba.
   - Abrir ejecución en Make → módulo 1 → copiar claves de `data`.
   - Actualizar escenario y esta doc si hay slug nuevo.
   - Confirmar 3 operaciones (trigger + parse teléfono + Sheets) cuando hay teléfono.

## Normalización → columnas Noco

Meta guarda respuestas en `1.data.<slug>` (slug = pregunta traducida). Noco usa columnas fijas: `email`, `phone`, `full_name`, `province`, `herd_count`, `livestock_type`.

| Columna Noco | Slugs Meta (orden de coalesce) |
|--------------|--------------------------------|
| `email` | `email`, `correo_electrónico`, `e-mail` |
| `phone` | `phone_number`, `phone`, `número_de_teléfono`, `numéro_de_téléphone` |
| `full_name` | `full_name`, `full name`, `nombre_y_apellidos`, o `prénom` + `nom_de_famille` |
| `province` | `province`, `provincia`, `region`, `localisation_d’élevage`, `τοποθεσία_της_κτηνοτροφικής_μονάδας` (formulario griego) |
| `herd_count` | ES/EN/PT/FR/EL/IT slugs de “cuántos animales…” (valor = `join(1.data.\`slug\`; ", ")`) |
| `livestock_type` | ES/EN/PT/FR/EL/IT slugs de tipo de ganado (mismo `join`) |

**Make (producción):** los tres escenarios (**7950608**, **7951407**, **7952998**) usan el mismo coalesce multi-idioma en el POST Noco (módulo 7). Para arrays Meta usar `join(1.data.\`slug\`; ", ")` — **no** `join(1.data.\`slug\`[]; …)` (devuelve vacío en HTTP Noco).

Formularios observados oct 2026: ES `930350286773221`, PT `4155466354724737`, EL `1995539671207390`, FR `2174360319708766`, INEA Baleares `1787294379178073` (slugs Meta EN: `animal_count`, `livestock_type` arrays).

**Backfill / scripts:** `scripts/digitanimal_field_aliases.py` + `digitanimal_noco_record.record_from_make_bundle()`; aplicar a filas existentes con `scripts/noco_normalize_from_meta.py` (lee `meta_payload_json.data`).

## Espejo NocoDB (`meta_leads`)

Tras el trigger Meta, los tres escenarios insertan en Noco (módulos **6** JSON + **7** HTTP) y siguen con Sheets:

| País | Escenario | Orden flow (inicio) |
|------|-----------|---------------------|
| ES | 7950608 | 1 → 6 → 7 → router (Sheets) |
| FR | 7951407 | 1 → 6 → 7 → teléfono → Sheets |
| IT | 7952998 | 1 → 6 → 7 → Sheets |

Scripts: `scripts/patch_make_noco_meta_leads.py`, `scripts/make_noco_sync_scenarios.py`. Token Noco vía env `NOCO_TOKEN` al parchear (migrar a Make Key en UI).

## Fix aplicado — España (7950608)

Router «Tiene teléfono / Sin teléfono» usa el coalesce anterior en filtro y en **Parse phone number**. Replay del lead que fallaba (`ceed6443…`) → **`9ff0519982a44a6abf0d3269db115a46`**, **SUCCESS**, **3 operaciones** (rama con parse).

Scripts locales: `scripts/patch_digitanimal_spain_phone_coalesce.py`.

## Hoja `meta_DigitanimalFR` — filas que no son campaña Francia

**Qué esperabas:** solo leads de formularios de la **página Meta Francia** (`page_id` **1323667177812599**), escenario Make **7951407** (hook **3901501**).

**Por qué ves otras filas:** el escenario **italiano** (**7952998**) se clonó del francés y, durante un tiempo, el módulo Google Sheets seguía apuntando a **`meta_DigitanimalFR`** aunque el webhook era el de la **página IT** (`100420486184506`). Esos leads son reales (p. ej. Calabria, nombres de campaña en español/italiano), pero **nunca pasaron por la página FR** — estaban en la pestaña equivocada por configuración Make, no porque Meta mezclara países en un mismo hook.

**Estado actual (oct 2026):** solo **7951407** escribe en `meta_DigitanimalFR`; **7952998** → `meta_DigitanimalIT`. Noco distingue bien por `make_scenario_id` / `page_id`. Las filas “raras” en FR son **históricas** (antes del cambio + posibles replays).

**Regenerar las tres pestañas (sin duplicados, por `page_id`):**

```bash
export NOCO_TOKEN=...
# Vista previa
python3 scripts/digitanimal_sheets_regenerate_from_noco.py --dry-run
# Export JSON (sin credenciales Google)
python3 scripts/digitanimal_sheets_regenerate_from_noco.py --export-json /tmp/matrices.json
# Escribir en Sheets (cuenta de servicio con acceso al spreadsheet)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
python3 scripts/digitanimal_sheets_regenerate_from_noco.py --write
```

Criterio: una fila por `leadgen_id` (Noco Id más alto gana); pestaña = `page_id` Meta (**ES** `1057071361086931`, **FR** `1323667177812599`, **IT** `100420486184506`). Columnas canónicas: mismas que `digitanimal_sheets_export_from_noco.py`.

## Pendientes recomendados

- **FR (7951407):** añadir router + coalesce `phone_number` / `numéro_de_téléphone`; revisar province (`localisation_d’élevage` vs columna province); alinear mapeo Sheets con columnas con nombre (como IT/ES) en lugar de índices `0`–`18`.
- **Sheets:** limpiar filas IT/otros países en `meta_DigitanimalFR` (ver sección anterior).
