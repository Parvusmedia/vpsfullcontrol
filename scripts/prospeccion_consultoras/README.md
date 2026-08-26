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
./run.sh contact --limit 4 --live  # envía (pausa 30–90s antes de cada invite)

## Segmento SME (colaboración externa vía Sales Navigator InMail)

```bash
./run.sh queries --segment sme
./run.sh preview-inmail --first-name Flor --tier deloitte_digital --country Spain
./run.sh discover --segment sme --max-queries 14 --max-per-query 6
./run.sh sync --segment sme
./run.sh list                # revisar en NocoDB (contact_type=sme_inmail)
./run.sh ready-inmail        # marca inmail_ready tras revisión
./run.sh inmail --limit 3    # dry-run InMail
./run.sh inmail --limit 3 --live  # envía InMail (Sales Navigator, pausa 30–90s)
```

### Email (Icypeas + Smartlead)

```bash
./run.sh create-smartlead-campaigns   # crea campañas ES + EN (PAUSED)
./run.sh provision-columns            # columnas email/smartlead en NocoDB
./run.sh enrich-email --limit 10        # dry-run Icypeas (score>=4, sme_inmail)
./run.sh enrich-email --limit 10 --live
./run.sh smartlead-enroll --limit 10    # dry-run enroll (requiere email)
./run.sh smartlead-enroll --limit 10 --live  # requiere CONSULTORAS_SMARTLEAD_ENABLED=true
```

Campañas Smartlead (PAUSED hasta activar):
- **ES** — países hispanohablantes, mismo copy que InMail + reminder 7 días
- **EN** — resto de geos, mismo copy que InMail + reminder 7 días

Env: `SMARTLEAD_CONSULTORAS_ES_CAMPAIGN_ID`, `SMARTLEAD_CONSULTORAS_EN_CAMPAIGN_ID`

Firmas: Deloitte Digital, Accenture Song, PwC, KPMG, everis/NTT DATA, Making Science, IDOM.
./run.sh poll-acceptances --live   # detecta aceptaciones → status accepted
./run.sh followup --live --limit 3 # mensaje tras aceptación (pausa antes de cada uno)
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

## Sales Navigator — búsquedas guardadas

Ver `data/sales_nav_searches.json`.

**Europa — Martech — consultoras digitales** (2025-08-25)
- Empresas: Deloitte Digital, IDOM, Making Science, Bain & Company, Accenture Song
- Seniority: Partner, CXO, VP, Director
- Región: Europe
- Keywords: `martech`
- [Abrir en Sales Navigator](https://www.linkedin.com/sales/search/people?query=(spellCorrectionEnabled%3Atrue%2CrecentSearchParam%3A(id%3A5838400562%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3ACURRENT_COMPANY%2Cvalues%3AList((id%3Aurn%253Ali%253Aorganization%253A2449847%2Ctext%3ADeloitte%2520Digital%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))%2C(id%3Aurn%253Ali%253Aorganization%253A12514%2Ctext%3AIDOM%2520Consulting%252C%2520Engineering%252C%2520Architecture%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))%2C(id%3Aurn%253Ali%253Aorganization%253A18505126%2Ctext%3AMaking%2520Science%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))%2C(id%3Aurn%253Ali%253Aorganization%253A2114%2Ctext%3ABain%2520%2526%2520Company%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))%2C(id%3Aurn%253Ali%253Aorganization%253A85405652%2Ctext%3AAccenture%2520Song%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A320%2Ctext%3AOwner%2520%252F%2520Partner%2CselectionType%3AINCLUDED)%2C(id%3A310%2Ctext%3ACXO%2CselectionType%3AINCLUDED)%2C(id%3A300%2Ctext%3AVice%2520President%2CselectionType%3AINCLUDED)%2C(id%3A220%2Ctext%3ADirector%2CselectionType%3AINCLUDED)))%2C(type%3AREGION%2Cvalues%3AList((id%3A100506914%2Ctext%3AEurope%2CselectionType%3AINCLUDED))))%2Ckeywords%3Amartech)&sessionId=YwVaKWptS6SKLnyNbGN9uw%3D%3D)

## Reglas

- Hard excludes: RRHH, audit, tax, cyber, data engineering, SAP, junior, sales director, manager genérico
- Score ≥ 4: mensaje de conexión generado, status `reviewed`
- Seeds (`source_query=seed:*`): no se re-scorean
- Límite práctico Unipile/LinkedIn: ~6 invitaciones/día
- Pausa aleatoria 30–90 s antes de **cada** acción Unipile (invite, poll, follow-up), en dry-run y live

## NocoDB

Tabla: `mj23ak5ilm76662` en `https://mpa.parvusmedia.com`
