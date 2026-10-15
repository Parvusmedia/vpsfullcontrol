# NocoDB `meta_leads` — espejo unificado Meta (Digitanimal)

| Recurso | ID |
|---------|-----|
| Workspace | `w1yr9d7k` |
| Base | `p62l2gyhjqj4vo1` |
| Tabla | `meta_leads` → **`mieilgjtcw04jjr`** |
| Vista UI | **`vwxg2zcslydyr6vd`** (no confundir con table id) |
| URL | https://mpa.parvusmedia.com/w1yr9d7k/p62l2gyhjqj4vo1 |

## Columnas unificadas (inglés, snake_case)

| Columna Noco | Tipo | Origen Make / Meta |
|--------------|------|---------------------|
| `leadgen_id` | Text | `{{1.leadgenId}}` (clave natural) |
| `form_id` | Text | `{{1.formId}}` |
| `page_id` | Text | `{{1.pageId}}` |
| `platform` | Text | `{{1.platform}}` |
| `is_organic` | Checkbox | `{{1.isOrganic}}` |
| `date_created` | DateTime | `{{1.dateCreated}}` |
| `lead_source` | Text | `meta_{{1.pageId}}` |
| `campaign_id` | Text | `{{1.campaignId}}` |
| `campaign_name` | Text | `{{1.campaignName}}` |
| `adset_id` | Text | `{{1.adsetId}}` |
| `adset_name` | Text | `{{1.adsetName}}` |
| `ad_id` | Text | `{{1.adId}}` |
| `ad_name` | Text | `{{1.adName}}` |
| `adgroup_id` | Text | `{{1.adgroupId}}` |
| `email` | Text | coalesce abajo |
| `phone` | Text | E.164 tras parser o coalesce raw |
| `full_name` | Text | coalesce abajo |
| `province` | Text | coalesce geo abajo |
| `herd_count` | Text | coalesce rebaño (valores unidos) |
| `livestock_type` | Text | coalesce tipo ganado |
| `home_listing` | Text | `{{1.homeListing}}` |
| `partner_name` | Text | `{{1.partnerName}}` |
| `retailer_item_id` | Text | `{{1.retailerItemId}}` |
| `make_scenario_id` | Text | Constante por escenario: `7950608`, `7951407`, `7952998` |
| `meta_payload_json` | JSON | Bundle completo del módulo 1 (ver Make) |

Columnas sistema Noco: `id`, `created_at`, `updated_at`, …  
`title` queda disponible para título de fila en UI (opcional: `{{full_name}}`).

## Coalesce Make (IML) — normalizar antes de Noco

**Email**

```text
{{ifempty(1.data.email; 1.data.`correo_electrónico`; 1.data.`e-mail`)}}
```

**Teléfono (raw, antes de parse)**

```text
{{ifempty(1.data.phone_number; 1.data.`número_de_teléfono`; 1.data.`numéro_de_téléphone`)}}
```

**Nombre**

```text
{{ifempty(1.data.full_name; 1.data.nombre_y_apellidos; trim(1.data.`prénom` & " " & 1.data.`nom_de_famille`))}}
```

**Provincia / geo**

```text
{{ifempty(1.data.province; 1.data.provincia; 1.data.region; 1.data.`localisation_d’élevage`)}}
```

**Cantidad animales** (ejemplo; ampliar slugs según forms)

```text
{{ifempty(1.data.`¿cuántos_animales_tienes?`[]; 1.data.`how_many_animals_do_you_have?`[]; 1.data.`quantos_animais_você_tem?`[]; 1.data.`combien_d’animaux_avez-vous_?`[]; 1.data.`número_de_animales:`[])}}
```

**Tipo ganado**

```text
{{ifempty(1.data.`¿qué_tipo_de_ganado_tienes?`[]; 1.data.`what_type_of_livestock_do_you_own?`[]; 1.data.`qual_o_tipo_de_gado_que_possui?`[]; 1.data.`quel_type_de_bétail_avez-vous_?`[])}}
```

**JSON crudo Meta**

Serializar el output del trigger (todo el bundle `1`) a JSON en Make (p. ej. módulo *JSON > Create JSON* o función `json`/`toString` según versión) y enviar al campo `meta_payload_json`.

## API

- Crear columnas (idempotente manual): `scripts/nocodb_meta_leads_create_columns.sh` con `NOCODB_API_TOKEN` (token con acceso a la base).
- Insertar fila: `POST /api/v2/tables/mieilgjtcw04jjr/records` con header `xc-token`.

## Próximos pasos

1. Añadir en escenarios Make **7950608**, **7951407**, **7952998** un módulo HTTP → Noco tras normalizar campos (mantener Sheets si hace falta).
2. Webhook Noco → BigQuery (fuente CRM).
3. Unificar forms Meta hacia slugs estándar (`email`, `phone_number`, `full_name`) para reducir coalesce.
