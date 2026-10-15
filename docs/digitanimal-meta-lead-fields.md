# Digitanimal — Meta Lead Ads: slugs de campos y nomenclatura

Carpeta Make: **Digitanimal** (`folderId` **404390**, team **38243**).

Escenarios:

| País | Escenario | ID | Hoja Google |
|------|-----------|-----|-------------|
| ES | Digitanimal_Spain_Meta-LeadAds | 7950608 | `meta_DigitanimalES` |
| FR | Digitanimal_FR_Meta-LeadAds | 7951407 | `meta_DigitanimalFR` |
| IT | Digitanimal_IT_Meta-LeadAds | 7952998 | *(revisar: hoy apunta a FR)* |

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

### Francia — formulario `1099884246301839` (sample + producción)

| Slug Meta | Uso en Sheets |
|-----------|----------------|
| `e-mail` | email |
| `prénom` | name (solo nombre; no se concatena `nom_de_famille` en el escenario) |
| `nom_de_famille` | *(presente en sample, no mapeado)* |
| `numéro_de_téléphone` | parse → `phone`; columna province recibe copia del raw en mapping actual |
| `localisation_d’élevage` | *(sample; no mapeado a province en FR)* |
| `combien_d’animaux_avez-vous_?` | cant-animales |
| `quel_type_de_bétail_avez-vous_?` | tipo_animal |

### Italia

Escenario clonado de FR (campos FR, hoja `meta_DigitanimalFR`, sin parser de teléfono). Al publicar formulario IT, **definir slugs italianos** o reutilizar tipos predefinidos Meta en inglés.

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

## Fix aplicado — España (7950608)

Router «Tiene teléfono / Sin teléfono» usa el coalesce anterior en filtro y en **Parse phone number**. Replay del lead que fallaba (`ceed6443…`) → **`9ff0519982a44a6abf0d3269db115a46`**, **SUCCESS**, **3 operaciones** (rama con parse).

Scripts locales: `scripts/patch_digitanimal_spain_phone_coalesce.py`.

## Pendientes recomendados

- **FR (7951407):** añadir router + coalesce `phone_number` / `numéro_de_téléphone`; revisar province (`localisation_d’élevage` vs columna province).
- **IT (7952998):** hoja `meta_DigitanimalIT`, campos IT o predefinidos Meta, parser teléfono `IT`.
