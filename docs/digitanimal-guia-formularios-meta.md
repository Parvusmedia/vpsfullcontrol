# Guía para crear formularios de leads en Meta (Digitanimal)

Documento para **quien diseña y publica formularios** en Meta Lead Ads. El objetivo es que todos los mercados envíen los **mismos nombres de campo** (slugs) y, cuando sea posible, las **mismas claves de opción**, para que Make/n8n y CRM no pierdan datos.

**Datos de referencia:** export API Meta, 15/10/2026 — 57 formularios, 2.358 leads (90 días). Detalle completo en [correlacion-campos-formularios.xlsx](./reference/correlacion-campos-formularios.xlsx) (pestañas *Campos base*, *Correlación de campos*, *Correlación de valores*, *Formularios Meta*).

**Integración técnica (Make, Noco, coalesce):** [digitanimal-meta-lead-fields.md](./digitanimal-meta-lead-fields.md).

---

## Reglas de oro (léelas antes de tocar el editor)

1. **Contacto = preguntas predefinidas de Meta**, no preguntas “personalizadas” con texto traducido.
2. **Slug del campo personalizado = nombre en inglés**, minúsculas, sin tildes: `livestock_type`, `animal_count`, `farm_size_ha`.
3. **Texto visible** para el ganadero: en el idioma del país (español, francés, italiano, etc.).
4. **País no se pregunta en el formulario.** Indícalo en el **nombre del formulario** con sufijo `_ES`, `_PT`, `_FR`, `_IT`, `_GR`, `_RO`, `_HR` o `_UK` (igual que la web con `origen_formulario`).
5. **No confíes en el “idioma del formulario”** de Meta para saber el mercado: Italia suele estar en `es_LA` y Grecia/Rumanía/Croacia en `es_ES`. El sufijo del nombre manda.
6. Si Meta permite **editar la clave interna de cada opción**, usa los valores de la sección [Valores unificados de las opciones](#valores-unificados-de-las-opciones). Si no, el equipo de integración traduce con la hoja *Correlación de valores* del Excel.

---

## Campos base (lista cerrada)

Estos campos cubren casi todos los leads. Los porcentajes son sobre los **2.358 leads** de los últimos 90 días.

| Slug (nombre del campo) | Qué preguntas | Tipo en Meta | ¿Obligatorio en captación estándar? |
|-------------------------|---------------|--------------|-------------------------------------|
| `email` | Email | **Email** (predefinida) | Sí |
| `phone_number` | Teléfono | **Phone number** (predefinida) | Sí |
| `full_name` | Nombre y apellidos | **Full name** (predefinida) | Sí (preferido) |
| `province` | Provincia / región de la explotación | **Province** (predefinida) | Sí, salvo campañas regionales IT 2026 |
| `livestock_type` | Tipo de ganado | Personalizada, **opciones fijas** | Sí (99 % de leads) |
| `animal_count` | Número de animales (tramos) | Personalizada, **opciones fijas** | Casi siempre (91 %) |

Hoy muchos formularios antiguos envían **otros slugs** (`correo_electrónico`, `número_de_teléfono`, `prénom`, `localisation_d’élevage`, etc.). Los formularios **nuevos** deben usar la tabla de arriba. Los 15 formularios que siguen recibiendo leads se **duplican** con estos nombres; el resto se puede **archivar**.

---

## Cómo configurar cada campo en el editor de Meta

### Email → slug `email`

- Añade la pregunta de tipo **Email** (no “Pregunta personalizada” con etiqueta “Correo electrónico”).
- No importa que la etiqueta visible diga “Email”, “E-mail” o “Correo”: lo importante es el **tipo Email** de Meta.
- **No uses** a la vez `email` y otra pregunta custom de correo.

### Teléfono → slug `phone_number`

- Tipo **Phone number** (predefinida).
- **Evita** duplicar: no mezcles “Phone number” y una pregunta custom “Número de teléfono” en el mismo formulario.

### Nombre → slug `full_name`

- Tipo **Full name** (predefinida), **también en Francia**.
- **No uses** `First name` + `Last name` salvo que sea imposible cambiar un formulario legacy; en formularios nuevos, un solo campo Full name.
- Si mantienes nombre/apellido separados, los slugs serían `first_name` y `last_name` (menos ideal para CRM unificado).

### Provincia → slug `province`

- Tipo **Province** (predefinida).
- **No uses** texto libre (“Localisation d’élevage”, “Provincia”, “Región”) para captación estándar: hoy FR/GR/IT mandan slugs distintos y el dato cuesta más de normalizar.
- Excepción: campañas que **deliberadamente** no piden provincia (regionales Italia 2026).

### Tipo de ganado → slug `livestock_type`

- Pregunta **personalizada**, tipo **opciones** (una o varias según campaña).
- **Nombre del campo (slug):** exactamente `livestock_type` en todos los mercados.
- **Texto de la pregunta:** traducido (ej. «¿Qué tipo de ganado tienes?», «Quel type de bétail…»).
- **Opciones visibles:** bovino, ovino, caprino, equino, otros (texto en idioma local).
- **Claves de opción (si Meta las deja fijar):** ver tabla más abajo (`cattle`, `sheep`, …).

### Número de animales → slug `animal_count`

- Pregunta **personalizada**, **opciones fijas** (no número libre).
- **Slug:** `animal_count`.
- **Tramos estándar** (texto visible traducido):

  | Texto orientativo (ES) | Clave propuesta |
  |------------------------|-----------------|
  | Hasta 20 | `up_to_20` |
  | 21 - 50 | `21_50` |
  | 51 - 100 | `51_100` |
  | Más de 100 | `more_than_100` |

---

## Valores unificados de las opciones

Meta envía la **clave de la opción**, no el texto que ve la persona. Esa clave suele ir en el idioma del formulario (`hasta_el_20`, `jusqu’à_20`, `fino_a_20`…). En formularios nuevos, fija estas claves si el editor lo permite:

### `livestock_type`

| Clave propuesta | Significado | Notas |
|-----------------|-------------|--------|
| `cattle` | Bovino | |
| `sheep` | Ovino | |
| `goats` | Caprino | |
| `horses` | Equino | |
| `other` | Otros | |

**Italia regional 2026:** a veces separan bovino carne/leche (`cattle (carne)` / `cattle (leche)`) u ovino+caprino juntos (`sheep_goats`). Corregir al unificar si la campaña lo permite.

### `animal_count`

| Clave propuesta | Tramo |
|-----------------|--------|
| `up_to_20` | Hasta 20 |
| `21_50` | 21 - 50 |
| `51_100` | 51 - 100 |
| `more_than_100` | Más de 100 |

**Italia regional 2026:** revisar tramos (`>20` como primera opción parece un error; solapamiento 20-50 / 50–100). Ajustar al duplicar el formulario.

**Báscula (otro producto):** escala distinta (`0_100`, `100_300`, `more_than_300`). Puede mantenerse; no mezclar con formularios de captación general sin avisar a integraciones.

---

## Nombre del formulario y mercado

Patrón recomendado:

```text
[Nombre descriptivo de campaña]_[PAÍS]
```

Ejemplos: `V3_FORMULARIO LEADS ADS_ES`, `Leads Calabria 2026_IT`, `Formulario Inglés-V.2_UK`.

Códigos de país: **ES, PT, FR, IT, GR, RO, HR, UK** (Reino Unido / inglés).

No añadas una pregunta “País” en el formulario Meta.

---

## Campos extra (solo si la campaña lo pide)

| Slug | Uso | Tipo |
|------|-----|------|
| `devices_needed` | Vallado virtual: para cuántos animales | Personalizada, opciones |
| `farm_size_ha` | Tamaño explotación (ha) — regionales IT 2026 | Personalizada |
| `main_need` | Necesidad principal — regionales IT 2026 | Personalizada |
| `self_employed_or_sme` | Autónomo o pyme — Kit Digital | Personalizada |
| `first_name` / `last_name` | Solo si no puedes usar `full_name` | Predefinidas |

Nombra siempre el slug en **inglés minúscula** aunque la etiqueta esté traducida.

---

## Errores frecuentes (evítalos)

| Error | Qué pasa | Qué hacer |
|-------|----------|-----------|
| Teléfono como pregunta custom traducida | Llega `número_de_teléfono` y falla el escenario | Usar **Phone number** |
| Email custom | Llega `correo_electrónico`, `e-mail`… | Usar **Email** |
| Provincia en texto libre | Slugs distintos por idioma (`localisation_d’élevage`, `region`…) | Usar **Province** |
| Pregunta de ganado con slug traducido | Cada país tiene un slug distinto | Slug fijo `livestock_type` |
| Confundir idioma Meta con país | IT en `es_LA`, GR en `es_ES` | Sufijo `_IT`, `_GR` en el nombre |
| Apóstrofo “normal” en FR/IT | Las claves legacy usan **`’`** (tipográfico) | Al comparar textos, normalizar apóstrofos |

---

## Checklist antes de publicar

- [ ] Nombre del formulario termina en `_ES`, `_PT`, `_FR`, `_IT`, `_GR`, `_RO`, `_HR` o `_UK`.
- [ ] Email, teléfono y nombre son tipos **Email**, **Phone number** y **Full name**.
- [ ] Provincia es tipo **Province** (si aplica a la campaña).
- [ ] Tipo de ganado: slug **`livestock_type`**; opciones con claves `cattle`, `sheep`, `goats`, `horses`, `other` si es posible.
- [ ] Nº animales: slug **`animal_count`**; tramos estándar y claves `up_to_20`, `21_50`, `51_100`, `more_than_100` si es posible.
- [ ] Enviar **1 lead de prueba** y avisar a integraciones con: **ID del formulario**, nombre y captura de las claves que llegan (o enlace a ejecución Make).
- [ ] Si es duplicado de un formulario activo, confirmar que el antiguo quedará **archivado** cuando el nuevo esté en anuncios.

---

## Formularios activos (90 días) — duplicar con nombres nuevos

Solo estos **15** han tenido leads recientes; son los que hay que **pasar** a la nomenclatura de esta guía. El resto (42) puede archivarse.

| Formulario | Mercado | Leads 90 d | Campos destacados |
|------------|---------|------------|-------------------|
| V3_FORMULARIO LEADS. ADS ESP | ES | 429 | ganado + nº animales |
| Leads IT-V2 | IT | 411 | todos los base |
| FORMULARIO LEADS. PT-V.2 | PT | 379 | ganado + nº animales |
| V4_Formulario Leads FR-copy | FR | 308 | nombre/apellido separados → unificar a `full_name` |
| V3_FORMULARIO LEADS. GR | GR | 256 | ubicación texto libre → `province` |
| V2_FORMULARIO LEADS. ADS ESP | ES | 139 | sin nº animales |
| Leads_FR_VV | FR | 123 | igual que FR-copy |
| Formulario Inglés-V.2 | GB | 84 | `region` → `province` |
| Leads Calabria 2026 | IT | 72 | + `farm_size_ha`, `main_need`; sin provincia |
| FORMULARIO LEADS. ADS GR | GR | 45 | solo ganado + contacto |
| FORMULARIO BASCULA LEADS. ADS ESP | ES | 35 | escala animales distinta |
| Formulario Inglés_SAT | GB | 31 | `email_address` → `email` |
| Leads Basilicata 2026 | IT | 27 | como Calabria |
| Leads Umbria 2026 | IT | 18 | como Calabria + email |
| ESP_Campaña GPS + Datanimal Gestión Ganadera | ES | 1 | estándar |

IDs y slugs actuales vs propuestos: pestaña **Formularios Meta** del Excel.

---

## Mientras no estén todos los formularios renombrados

Integración puede seguir recibiendo leads **sin pérdidas**:

1. **Contacto:** leer una vez el catálogo del formulario (`GET /{form_id}?fields=questions`) y mapear **por tipo** Meta (`EMAIL`, `PHONE`, `FULL_NAME`, `PROVINCE`), no por nombre del slug.
2. **Ganado y nº animales:** usar el Excel (*Correlación de campos* + *Correlación de valores*) como tabla de búsqueda.

---

## Web (Contact Form 7)

Aplicar los **mismos slugs propuestos** en la web cuando se unifique con Meta. Referencia en el Excel, pestaña **Web (CF7)** (`your-email` → `email`, `tipo[]` → `livestock_type`, sufijo de `origen_formulario` para país, etc.).

---

## Resumen visual (formulario estándar)

```text
┌─────────────────────────────────────────┐
│  Meta Lead Form — [Campaña]_ES          │
├─────────────────────────────────────────┤
│  livestock_type   (custom, opciones)    │
│  animal_count     (custom, tramos)      │
│  full_name        (Full name)           │
│  email            (Email)               │
│  phone_number     (Phone number)        │
│  province         (Province)              │
└─────────────────────────────────────────┘
         País = sufijo del nombre del form
         Etiquetas visibles = idioma local
         Slugs = tabla «Campos base»
```

---

*Última revisión: octubre 2026 — alineado con correo de operaciones Meta y export `correlacion-campos-formularios.xlsx`.*
