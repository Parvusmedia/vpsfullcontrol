# Prospección Consultoras

Pipeline Harvest → scoring estricto → NocoDB (`mj23ak5ilm76662`).

## Comandos (en VPS)

```bash
cd /opt/apps/prospeccion-consultoras
./run.sh provision-columns   # primera vez
./run.sh queries             # ver búsquedas Harvest
./run.sh seed                # 5 contactos prioritarios Deloitte
./run.sh discover --max-queries 11 --max-per-query 6
./run.sh sync
./run.sh rescore             # re-aplica hard excludes (no toca seeds)
./run.sh ready               # marca score>=4 como connection_ready
./run.sh contact --limit 4   # dry-run invitaciones Unipile
./run.sh contact --limit 4 --live  # envía (máx 4 por ejecución; respeta límites LinkedIn)
./run.sh list
```

## Reglas

- Hard excludes: RRHH, audit, tax, cyber, data engineering, SAP, junior, sales director, manager genérico
- Score ≥ 4: mensaje de conexión generado, status `reviewed`
- Seeds (`source_query=seed:*`): no se re-scorean
- Envío manual: `ready` → `contact` (dry-run) → `contact --live` (máx ~6/día vía Unipile)

## NocoDB

Tabla: `mj23ak5ilm76662` en `https://mpa.parvusmedia.com`
