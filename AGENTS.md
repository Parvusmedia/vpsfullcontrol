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

## Gaggle demo (Publora advocacy)

Repo path: `gaggle-demo/`. Public demo URL: **https://ngaged.pmediaplus.com** (DNS A → Parvus `87.106.194.137`). VPS: `/opt/apps/gaggle-demo`, secrets `/opt/apps/private/gaggle-demo/publora.env`, systemd `gaggle-demo.service` (:8790), nginx `ngaged.pmediaplus.com`.

Deploy: `deploy-demo.sh` then `deploy/install-ngaged-vhost.sh` on `parvus-vps`.

### Email SMTP (2FA admin y campañas)

Buzón Plesk: **`alerts@pmediaplus.com`** → `mail.pmediaplus.com:587` (TLS). En prod: `NGAGED_SMTP_*` y `NGAGED_MAIL_FROM` en `publora.env`. Plantillas: `gaggle-demo/deploy/publora.env.example`, `deploy/configure-plesk-smtp.sh`.

Cloud Agents: pedir la contraseña con **environment secret** `NGAGED_SMTP_PASSWORD` (panel de secrets / `request-environment-setup-actions`), nunca en el chat. Aplicar en el VPS con `configure-plesk-smtp.sh` vía `ssh parvus-vps` sin imprimir la clave. Comprobar: `GET /api/health` (`smtpConfigured`) o email de prueba en Ajustes.

No commitear ni loguear `NGAGED_SMTP_PASSWORD`.
