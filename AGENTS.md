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

### n8n API / tokens — discover before blocking

**Do not tell the user that n8n (or another) access is missing until you have actively searched** in the Cloud Agent env, on the VPS, and in related project configs.

Search order (n8n):

1. Cloud Agent: `scripts/n8n status`; env vars `N8N_URL`, `N8N_REST_API_KEY`, `N8N_MCP_TOKEN`, `N8N_API_KEY` (JWT `mcp-server-api` vs `public-api` vs `n8n_api_…`).
2. MCP direct: `POST {N8N_URL}/mcp-server/http` with `Accept: application/json, text/event-stream` if the unified script MCP probe fails with 406.
3. VPS Parvus (`ssh parvus-vps`): `/opt/apps/nextconvers-qualification-gate/config/deployment.local.env` (`N8N_BASE_URL`, `N8N_API_KEY` REST JWT). Other products may use similar `deployment.local.env` or `config/*.env` under `/opt/apps/*` — locate by name, never paste values.
4. Docs in-repo: `docs/N8N_ONE_WINDOW.md`, `docs/n8n/SMARTLIFE_RADIADOR.md`.

Only after those steps fail should you ask the user for a new secret or say you cannot proceed. When reporting blockage, list **what you already checked** (paths and mechanisms, not secret values).

## Access discovery (general)

For any missing API, token, or credential:

1. Repo scripts, `AGENTS.md`, and `docs/`.
2. Cloud Agent / team secrets (`N8N_*`, etc.) and `cursor-cloud` list-available-secrets when relevant.
3. VPS `ssh parvus-vps`: `/opt/apps/private/`, `/opt/apps/<product>/config/`, `deploy/*.env.example` for filenames only; read values only inside remote commands, never echo in chat or commits.
4. MCP / plugin auth (e.g. N8N MCP OAuth) if REST from env fails — fix or use an alternate channel found on the VPS.

Same rule: **search first, then report** what is missing and what was tried.

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
