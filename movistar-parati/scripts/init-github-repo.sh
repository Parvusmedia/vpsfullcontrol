#!/usr/bin/env bash
# Tras crear el repo vacío en GitHub: Parvusmedia/movistar-parati
set -euo pipefail
cd "$(dirname "$0")/.."
git init
git add .
git commit -m "Initial commit: Movistar Para Ti (NocoDB + Telegram)"
git branch -M main
git remote add origin git@github.com:Parvusmedia/movistar-parati.git
git push -u origin main
