# Prospección CDE SalesNav (EN)

Pipeline GTM para [companydataenrichment.com/salesnav](https://companydataenrichment.com/salesnav/):

**Unipile Sales Navigator search → filtro `premium=true` + empresa ≥11 + no LinkedIn → NocoDB (pendiente) → Smartlead / Unipile.**

## Prueba actual

```bash
cd /opt/apps/prospeccion-cde-salesnav
./run.sh queries
./run.sh discover --max-keep 20 --max-raw 80
```

Cuenta Unipile: `rq1lQcYTToC9hlWD4vO94g`. Dry-run de contacto todavía no: esta oleada solo valida ICP.

## ICP

- US / UK / Europe, English profile
- Company headcount 11+ (prioridad 51–500)
- Sales / SDR / RevOps seniority manager+
- Hard exclude: LinkedIn, intern/junior/recruiter hiring, **`premium != true`**
