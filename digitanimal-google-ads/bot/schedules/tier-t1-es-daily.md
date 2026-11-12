---
cron: "0 7 * * 1-5"
---

Corrida programada T1 España (tier-t1-es-daily, 08:00 Europe/Madrid ≈ 07:00 UTC).

1. `compare_to_brief` con `pais: "ES"`.
2. `windsor_query_guide` tier T1 → consultas Windsor MCP últimos 7 días.
3. Analizar ritmo y conversiones; `propose_change` solo si procede.
4. Resumen corto por campaña; sin aplicar mutaciones sin sesión humana.
