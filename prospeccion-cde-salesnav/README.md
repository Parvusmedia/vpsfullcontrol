# Prospección CDE SalesNav (EN)

Pipeline GTM para [companydataenrichment.com/salesnav](https://companydataenrichment.com/salesnav/):

**Unipile Sales Navigator search → filtro `premium=true` + empresa ≥11 + no LinkedIn → NocoDB (pendiente) → Smartlead / Unipile.**

## Prueba de discover (2026-09-03)

```bash
cd /opt/apps/prospeccion-cde-salesnav
./run.sh queries
./run.sh discover --max-keep 20 --max-raw 80
```

Resultado en VPS: **26 raw → 20 kept**, 5 `not_premium`, 1 falso `intern` en “International” (ya corregido con word boundary). Unipile no devuelve headcount en el item de search; el filtro 11+ va en la query SN.

Cuenta Unipile: `rq1lQcYTToC9hlWD4vO94g`. Sin invites ni Smartlead en esta oleada.

## ICP

- US / UK / Europe, English profile
- Company headcount 11+ (prioridad 51–500)
- Sales / SDR / RevOps seniority manager+
- Hard exclude: LinkedIn, intern/junior/recruiter hiring, **`premium != true`**
