# AGENTS.md

## n8n default workflow (this repository)

When a user request is related to n8n (for example: "n8n", "workflow", workflow IDs, exports, MCP, REST API), use the unified helper command in this repository instead of calling n8n endpoints directly.

### Required first step

Run:

```bash
scripts/n8n status
```

This confirms whether MCP token, REST API key, or both are available.

### Standard commands

- List workflows: `scripts/n8n list --limit 50`
- Workflow details: `scripts/n8n details --workflow-id <id>`
- Export workflows: `scripts/n8n export --out /workspace/n8n_export_latest`

### Guardrails

- Prefer `scripts/n8n` over ad-hoc curl or custom n8n API calls.
- Do not print secret values.
- If `scripts/n8n` fails, report the failure and only then fall back to direct endpoint debugging.

## NocoDB MCP (base demos)

Cloud Agents do not support `mcp-remote`. Talk to NocoDB over HTTP MCP with `xc-mcp-token`. Native Cursor MCP must be added as an **HTTP** server in [cursor.com/agents](https://cursor.com/agents) (MCP dropdown) or Team Integrations. Until that native server is attached to the run, use the repo helper.

### Required first step

Run:

```bash
scripts/nocodb status
```

This confirms the HTTP MCP endpoint is reachable (token from env or `.cursor/mcp.json`) and the 11 record tools respond.

### Standard commands

- Base info: `scripts/nocodb base`
- List tables: `scripts/nocodb tables`
- Table schema: `scripts/nocodb schema --table-id <id>`
- Query records: `scripts/nocodb query --table-id <id> --page-size 10`
- Generic tool: `scripts/nocodb call --name <tool> --args '{...}'`

### Guardrails

- Prefer `scripts/nocodb` over ad-hoc curl or `npx mcp-remote`.
- Do not print `NOCODB_MCP_TOKEN` or `xc-mcp-token`.
- Do not create/update/delete records unless the user explicitly asked.
- Details: `docs/NOCODB_MCP.md`
