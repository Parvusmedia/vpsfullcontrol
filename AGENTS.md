# vpsfullcontrol

This repository is a **CI/CD control repo**, not an application. It contains only GitHub Actions workflow YAML that deploys and operates services on a self-hosted VPS. The actual application source lives in **external** repos (`Parvusmedia/agentv3`, `Parvusmedia/prosegurlatam`).

Files:
- `.github/workflows/deploy-agentv3.yml` — manual (`workflow_dispatch`) deploy of `agentv3` → `/opt/ai-agent-v3`, restarts `ai-agent-v3.service`, health-checks `http://127.0.0.1:8004/`.
- `.github/workflows/deploy-prosegurlatam.yml` — manual deploy of `prosegurlatam` → `/home/cursorbot/prosegurlatam`, seeds `data/*.json`, restarts `client-ficha-panel.service`, health-checks `http://127.0.0.1:8015/`.
- `.github/workflows/vps-ops.yml` (and a duplicate at repo root `vps-ops.yml`) — manual `status|logs|health|restart` via `sudo /usr/local/sbin/svcopctl <service> <action>`.

## Cursor Cloud specific instructions

- **There is nothing to build or run locally.** No package manifests, no dependencies, no app server. The only development activity is editing/validating the workflow YAML.
- **Lint/validate the workflows** (tools installed by the update script into `~/.local/bin`, which may not be on `PATH` — invoke by full path or `export PATH="$HOME/.local/bin:$PATH"`):
  - `actionlint` — GitHub Actions linter. Run from repo root: `actionlint`.
  - `yamllint -d relaxed vps-ops.yml .github/workflows/`.
- **Expected/benign actionlint finding:** `label "vps-ops" is unknown` on `runs-on: [self-hosted, vps-ops]` in `vps-ops.yml`. `vps-ops` is a legitimate custom label for the self-hosted runner; actionlint just doesn't know it. Do not "fix" it by changing the label.
- **The workflows cannot be dispatched/tested from this VM.** They require: self-hosted runners (labels `self-hosted`, `vps-ops`), the target VPS (systemd, `svcopctl`, ports 8004/8015), access to the external product repos, and secrets `AGENTV3_REPO_TOKEN` / `PROSEGURLATAM_REPO_TOKEN`. The most you can verify locally is (a) linting and (b) running the inline bash step logic (e.g. the `curl` health-check loop) against a local server.
- `gh workflow list` works read-only and shows all three workflows as `active` on the default branch.
