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

```bash
export N8N_URL=https://pmedia.app.n8n.cloud
export N8N_API_KEY=...
python3 scripts/deploy_linkedin_applicants_workflow.py
```

## Configurar nodo `Config`

| Variable | Descripción |
|----------|-------------|
| `unipile_dsn` | DSN de Unipile (ej: `api1.unipile.com`) |
| `unipile_api_key` | Access Token de Unipile |
| `unipile_account_id` | ID cuenta LinkedIn en Unipile (`acc_xxx`) |
| `linkedin_job_id` | ID de la oferta (ej: `4456186543`) |
| `openai_api_key` | Token de ChatGPT / OpenAI |
| `openai_model` | Modelo (por defecto `gpt-4o-mini`) |
| `job_title` | Título del puesto |
| `job_criteria` | Criterios must-have / nice-to-have |
| `google_sheet_id` | ID del spreadsheet de Google |
| `sheet_name` | Pestaña (por defecto `Candidatos`) |

## Google Sheet

Crea una hoja con estas columnas en la primera fila:

`application_id | nombre | perfil_url | headline | email | telefono | fecha_aplicacion | score | recomendacion | por_que_si | por_que_no | resumen | argumento | fecha_analisis`

Conecta credencial **Google Sheets OAuth2** en los nodos `Read Existing IDs` y `Append to Google Sheet`.

## Pipeline

```
Manual Trigger / Cron 30 min
  → Config
  → Read Existing IDs (dedup)
  → Fetch Applicants (Unipile, ratings=UNRATED)
  → Split and Filter New
  → Prepare AI Prompt
  → OpenAI Analysis
  → Parse AI Response
  → Append to Google Sheet
```

## Notas

- Solo procesa candidatos con rating `UNRATED` en LinkedIn.
- Evita duplicados comparando `application_id` con la hoja.
- El token de ChatGPT va en el nodo `Config`, no en credenciales de n8n.
- Ajusta `job_criteria` según el puesto concreto.
