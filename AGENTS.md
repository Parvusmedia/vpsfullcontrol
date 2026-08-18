# AGENTS.md

## Token-efficient reads

Read only what the task needs. Extra reads burn tokens.

- Locate with Glob/Grep first. Do not dump the repo or re-read files already in context.
- Read bounded spans (`offset`/`limit`). After an edit, do not re-read the whole file to confirm.
- Small change: one function/file. New work: copy 1–2 existing patterns, do not survey everything first.
- No Explore/Task subagents for a few-step edit. Inherit the parent model if a subagent is required.
- n8n: `scripts/n8n status`, then `details --workflow-id`. Do not list/export unless asked.

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
