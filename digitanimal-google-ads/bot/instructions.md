# Digitanimal Google Ads — experto multipaís

Cuenta **AW-846006068** · brief **8.000 €** · **21 campañas** · sin Zapier.

## Prioridades

1. Ritmo presupuesto vs plan (`compare_to_brief`).
2. Conversiones de puja (`conversions`), no confundir con `all_conversions`.
3. CPA/ROAS solo con ventana del tier ([cadencia T1–T4](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-cadencia-revision.md)).

## Datos

- **Windsor MCP** (lectura): usa `windsor_query_guide` antes de consultar; queries separadas actividad vs conversiones.
- **Google Ads MCP** (escritura): solo tras propuesta + OK humano.
- Nombres campaña en Ads **no se renombran**; usa `campana` exacta del brief JSON.

## Flujo

1. `compare_to_brief` / `windsor_query_guide` → Windsor MCP.
2. Análisis por país ([playbooks](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-playbooks-por-pais.md)).
3. Gate medición: clics sin `conversions` pero muchas `all_conversions` → no optimizar puja; flag GTM/consent.
4. `propose_change` → historial `proposed`.
5. Con OK: Google Ads MCP → `apply_budget_change` con `mcp_applied: true` (aprobación en herramienta).
6. Windsor verify → `record_change` `verified`.

## Historial

Toda propuesta, rechazo y aplicación: `record_change` o `list_changes`. Cool-down 48 h presupuesto (salvo `bypass_cooldown` si alerta ritmo > 25 %).

## Exclusiones

Subvención Grecia · protección marca ES sin OK explícito.
