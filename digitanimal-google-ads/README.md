# digitanimal-google-ads

Agente Agent SDK para análisis y optimización Google Ads (Digitanimal).

## Documentación (Project store)

- [Runbook](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-agent-runbook.md)
- [Cadencia](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-cadencia-revision.md)
- [Playbooks](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-playbooks-por-pais.md)
- [Historial](/cursor/stores/bc-86989293-16f2-44b9-b12a-fc100adc8e00/docs/google-ads-cambios-historico.md)

## MCP

Conectar en Cursor: **Windsor**, **Google Ads**. Archivos `bot/mcp-connections/windsor.ts`, `google-ads.ts`.

## Local

```bash
cd digitanimal-google-ads
npx @grok/agent-sdk validate --dir .
npx @grok/agent-sdk tool call compare_to_brief --dir . --input '{}'
```

Brief: `bot/lib/brief-campaigns.json` (21 campañas).
