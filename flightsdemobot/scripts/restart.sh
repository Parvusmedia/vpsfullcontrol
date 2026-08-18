#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
sudo systemctl restart flightsdemobot.service
sudo systemctl status flightsdemobot.service --no-pager -l | sed -n '1,30p'
