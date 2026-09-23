#!/usr/bin/env bash
# Fail deploy if Sales Nav landing regressed (FAQ removed, wrong asset versions, etc.)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LANDING="$ROOT/public/salesnav/index.html"
PANEL="$ROOT/public/salesnav/panel/index.html"
FRAG="$ROOT/public/salesnav/_faq-section.fragment.html"

fail() { echo "check-salesnav-landing: $*" >&2; exit 1; }

[[ -f "$LANDING" ]] || fail "missing $LANDING"
[[ -f "$PANEL" ]] || fail "missing $PANEL"
[[ -f "$FRAG" ]] || fail "missing FAQ fragment $FRAG"

grep -q 'id="faq"' "$LANDING" || fail "landing must include section id=faq"
grep -q 'faq-section' "$LANDING" || fail "landing must include .faq-section"
grep -q 'data-i18n="nav.faq"' "$LANDING" || fail "landing nav must link to #faq"
grep -q 'SN_FAQ_FRAGMENT' "$LANDING" || fail "landing FAQ must use SN_FAQ_FRAGMENT markers (run sync-salesnav-faq.py)"
grep -q 'openai-ads.js' "$LANDING" || fail "landing must include openai-ads.js"

# Panel FAQ must stay in sync with fragment markers
grep -q 'SN_FAQ_FRAGMENT' "$PANEL" || fail "panel FAQ must use SN_FAQ_FRAGMENT markers"

# Avoid accidental downgrade of salesnav.js on landing vs panel
landing_js=$(grep -oE 'salesnav\.js\?v=[0-9]+' "$LANDING" | head -1)
panel_js=$(grep -oE 'salesnav\.js\?v=[0-9]+' "$PANEL" | head -1)
[[ -n "$landing_js" && -n "$panel_js" ]] || fail "could not read salesnav.js cache versions"
if [[ "$landing_js" != "$panel_js" ]]; then
  fail "salesnav.js version mismatch: landing=$landing_js panel=$panel_js"
fi

echo "check-salesnav-landing: OK"
