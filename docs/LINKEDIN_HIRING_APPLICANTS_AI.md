# LinkedIn Hiring Applicants AI (n8n)

Workflow para analizar candidaturas de LinkedIn Hiring con Unipile + ChatGPT y guardar resultados en Google Sheets.

Archivo: [`n8n/workflows/linkedin-hiring-applicants-ai.json`](../n8n/workflows/linkedin-hiring-applicants-ai.json)

## Importar o desplegar

### Opción A — Import manual

1. n8n → **Workflows** → **Import from File**
2. Selecciona `linkedin-hiring-applicants-ai.json`
3. Configura el nodo `Config` y credenciales Google Sheets
4. **Activa** el workflow

### Opción B — Deploy por API

Crea `config/n8n.local.env` (ver [`docs/N8N_ONE_WINDOW.md`](N8N_ONE_WINDOW.md)) y ejecuta:

```bash
python3 scripts/deploy_n8n_workflows.py
```

## Configurar nodo `Config`

| Variable | Descripción |
|----------|-------------|
| `unipile_dsn` | DSN de Unipile (copiar del dashboard, ej: `api46.unipile.com`) |
| `unipile_port` | Puerto del DSN (copiar del dashboard, ej: `17682`). **Obligatorio** en HTTPS 443 |
| `unipile_api_key` | Access Token de Unipile |
| `unipile_account_id` | ID cuenta LinkedIn en Unipile (`acc_xxx`) |
| `linkedin_job_id` | ID de la oferta (ej: `4456186543`) |
| `openai_api_key` | Token de ChatGPT / OpenAI |
| `openai_model` | Modelo (por defecto `gpt-4o-mini`) |
| `job_title` | Título del puesto |
| `job_criteria` | Criterios must-have / nice-to-have |
| `google_sheet_id` | `1a6dDwT5VWQH5YMGx1kX-7HVVnozD-bspuzPLThjL1bQ` |
| `sheet_name` | `gid=0` (primera pestaña) |

## Google Sheet

Hoja: https://docs.google.com/spreadsheets/d/1a6dDwT5VWQH5YMGx1kX-7HVVnozD-bspuzPLThjL1bQ/edit

Inicializar cabeceras (si hace falta):

```bash
python3 scripts/init_candidatos_sheet_headers.py
```

Columnas en fila 1:

`application_id | nombre | perfil_url | headline | email | telefono | fecha_aplicacion | score | recomendacion | por_que_si | por_que_no | resumen | argumento | fecha_analisis`

Conecta credencial **Google Sheets OAuth2** en los nodos `Read Existing IDs` y `Append to Google Sheet`.

## Pipeline

```
Manual Trigger / Cron 30 min
  → Config ─┬→ Read Existing IDs (dedup, en paralelo)
            └→ Fetch Applicants (Unipile)
  → Split and Filter New
  → Prepare AI Prompt
  → OpenAI Analysis
  → Parse AI Response
  → Append to Google Sheet
```

**Importante:** `Read Existing IDs` y `Fetch Applicants` corren en paralelo desde `Config`. Si la hoja está vacía, el flujo ya no se corta antes de llamar a Unipile.

## Notas

- Procesa candidatos con cualquier rating (`UNRATED`, `MAYBE`, `GOOD_FIT`, `NOT_A_FIT`).
- Si Unipile devuelve **502**, falta `unipile_port` o el DSN es incorrecto.
- Si devuelve **503 No client session**, reconecta la cuenta LinkedIn en Unipile y verifica DSN/puerto/account_id.
- Evita duplicados comparando `application_id` con la hoja.
- El token de ChatGPT va en el nodo `Config`, no en credenciales de n8n.
- Ajusta `job_criteria` según el puesto concreto.
