# Prospección Consultoras

Pipeline Harvest → scoring estricto → NocoDB (`mj23ak5ilm76662`).

## Comandos (en VPS)

```bash
cd /opt/apps/prospeccion-consultoras
./run.sh provision-columns   # primera vez / nuevas columnas
./run.sh queries             # ver búsquedas Harvest
./run.sh seed                # 5 contactos prioritarios Deloitte
./run.sh discover --max-queries 11 --max-per-query 6
./run.sh sync
./run.sh rescore             # re-aplica hard excludes (no toca seeds)
./run.sh ready               # marca score>=4 como connection_ready
./run.sh contact --limit 4   # dry-run invitaciones Unipile
./run.sh contact --limit 4 --live  # envía (delay 30–90s entre invites)
./run.sh poll-acceptances --live   # detecta aceptaciones → status accepted
./run.sh followup --live --limit 3 # mensaje tras aceptación (status followup_sent)
./run.sh outreach --live             # poll + followup + contact (cron diario)
./run.sh list
```

## Flujo outreach

1. `ready` → revisión manual opcional en NocoDB
2. `contact --live` → `connection_sent` (+ delay aleatorio entre invites)
3. `poll-acceptances --live` → si Unipile devuelve 1º grado / relación → `accepted`
4. `followup --live` → envía `followup_message` → `followup_sent`

Por defecto el follow-up se envía en la misma pasada tras detectar la aceptación (`--min-hours-after-accept 0`). Para esperar 24h: `--min-hours-after-accept 24`.

Cron VPS (L–V 10:40 Europe/Madrid): `scripts/unipile-drain.sh`

## Reglas

- Hard excludes: RRHH, audit, tax, cyber, data engineering, SAP, junior, sales director, manager genérico
- Score ≥ 4: mensaje de conexión generado, status `reviewed`
- Seeds (`source_query=seed:*`): no se re-scorean
- Límite práctico Unipile/LinkedIn: ~6 invitaciones/día

## NocoDB

Tabla: `mj23ak5ilm76662` en `https://mpa.parvusmedia.com`
