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

## Shared VPS secrets (Icypeas / CDE)

Cross-project agent access on Parvus VPS (`ssh parvus-vps`):

- **Icypeas API key:** `/opt/apps/private/cde/icypeas.env` (`ICYPEAS_API_KEY`)
- **CDE production (Sales Nav):** `/var/www/vhosts/companydataenrichment.com/private/cde/icypeas.env` on `nextconvers-vps`
- **Mail tier code:** `cde-salesnav/public/api/_icypeas.php` (email-search + poll read)

Read with `grep ICYPEAS_API_KEY= /opt/apps/private/cde/icypeas.env` — never echo the value in chat, commits, or logs. Example template: `cde-salesnav/deploy/icypeas.env.example`.

## Sales Navigator panel (CDE)

Repo path: `cde-salesnav/`. Production: https://companydataenrichment.com/salesnav/panel/

### LinkedIn reconnect (ops)

When a user reconnects LinkedIn but the panel still shows disconnected:

1. Check `private/cde/salesnav_accounts.json` for their wallet (`em_` + sha256(email)).
2. If `invalid_at` is set but the Unipile seat is alive, loading the panel or calling `salesnav-status.php` should auto-recover (clears `invalid_at`).
3. Fallback: `deploy/recover-stale-linkedin.php <email>` on prod (PHP 8.3).

Primary sync path: Unipile webhook `POST /api/salesnav-unipile-notify.php` on `CREATION_SUCCESS` / `RECONNECTED`. Notify secret in `private/cde/unipile.env` (`SALESNAV_NOTIFY_SECRET`). Do not expose secrets or Unipile internals in user-facing copy.

### Deploy

```bash
cde-salesnav/deploy-salesnav-prod.sh
```

Use PHP 8.3 CLI on prod for maintenance scripts (`/opt/plesk/php/8.3/bin/php`).
