# Prospeccion Reckitt CDE

Oleada puntual Parvus Media: lista CDE Sales Navigator **Global Reckit Marketing & Media & Advertising**.

**CSV (`tsk_fb6268304961e568`) → Icypeas (si falta email) → Smartlead / Unipile**

Clona el patrón de `prospeccion-alarmas`. No reutiliza campañas Gift / NextConvers / Alarmas.

## Producto (ángulo, EN)

Ayudamos a Reckitt en España a **planificar medios a 7 días** y activar campañas data-driven conectadas a **weather + Google Trends en tiempo real**, para saber en qué región estará la demanda.

Campaña Smartlead: `CDE · Reckitt SN list · Data for Media · EN` — se crea **PAUSED**.

## Setup (VPS)

```bash
cd /opt/apps/prospeccion-reckitt-cde
chmod +x run.sh scripts/*.sh
cp .env.example .env
# RECKITT_UNIPILE_ACCOUNT_ID = seat CDE de emiliano@parvusmedia.com
# SMARTLEAD_RECKITT_EMAIL_ACCOUNT_ID = mailbox de Emiliano (no el campaign id de Alarmas)
./scripts/fetch-cde-csv.sh
./run.sh confirm
```

CSV prod (no commitear):  
`/var/www/vhosts/companydataenrichment.com/private/cde/salesnav_exports/tsk_fb6268304961e568.csv`

## Flujo diario

```bash
# 0) Traer CSV + importar (relevante=Sí; lista ya curada)
./scripts/fetch-cde-csv.sh
./run.sh import-csv

# 1) Config sin secretos + copy Smartlead
./run.sh confirm

# 2) Crear campaña dedicada (una vez, queda PAUSED)
./run.sh create-smartlead --dry-run
./run.sh create-smartlead
# SMARTLEAD_RECKITT_CAMPAIGN_ID=<id>  (también en data/smartlead_campaign.json)

# 3) Contact dry-run (nunca --live hasta OK)
./run.sh contact --limit 5
./run.sh contact --limit 50

# 4) Tras OK de copy email:
#    en .env: RECKITT_SMARTLEAD_ENABLED=true
./run.sh contact --limit 10 --live

# 5) LinkedIn: draft notes → revisión humana → cola → drain
./run.sh compose-messages
./run.sh compose-messages --live
# En data/leads.json: mensaje_estado=Confirmado
./run.sh queue-unipile
./run.sh unipile-drain
./run.sh unipile-drain --limit 10 --live
```

Orden de `contact`:

1. Email ya en CSV (`work_email`) → Smartlead enroll  
2. Si no hay email y `--live` → Icypeas (`firstname` + `lastname` + `reckitt.com` / `company_domain`)  
3. Si Icypeas falla y hay patrón en el mismo dominio → guess  
4. Si hay email → Smartlead  
5. Si no → Unipile (mejor vía `queue-unipile` + `unipile-drain`)

## Lista (43 filas)

| Canal | Count | Plan |
|-------|------:|------|
| Email Icypeas/Proofpoint (`work_email`) | 7 | Enroll Smartlead (dry-run primero) |
| Icypeas `not_found` | 8 | Cola Unipile (invite + follow-up) |
| Icypeas `error` | 28 | Reintento Icypeas en `--live`, si no → Unipile |

Dominio email visto: `reckitt.com`. Caps Unipile: **10/día**, **3/hora**.

## Caps / Unipile

Límites en NocoDB `automation_limits` (mismas tablas que Alarmas, **workflow nuevo**):

- Workflow `reckitt_cde_unipile_connection_invites`
- Seat: CDE panel `emiliano@parvusmedia.com` (`RECKITT_UNIPILE_ACCOUNT_ID`)
- **No** usar `UNIPILE_ACCOUNT_ID` de `/etc/linkedinreport/app.env` (otro wallet)
- Drain live exige `mensaje_estado=Confirmado`

Cron opcional (no instalado por defecto):

`15 10,12,14,16 * * 1-5 /opt/apps/prospeccion-reckitt-cde/scripts/unipile-drain.sh`

## Flags

- `RECKITT_DRY_RUN=true` por defecto; `--live` solo tras resumen
- `RECKITT_SMARTLEAD_ENABLED=false` hasta OK de copy
- Campaña Smartlead **nueva**; nunca `SMARTLEAD_ALARM_WA_CAMPAIGN_ID`

## Tests

```bash
cd /opt/apps/prospeccion-reckitt-cde
python3 -m unittest discover -s tests -v
```
