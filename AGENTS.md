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

## Cursor Cloud specific instructions

Do not record screen videos or upload walkthrough screenshots for routine UI, copy, or layout tweaks (including the live-fare demo/banner) unless the user explicitly asks for a visual demo.

For those changes, automated tests plus a live URL or log check are enough. Only produce screenshot/video artifacts when the user requests them, or when a GUI bug cannot be verified any other way.
