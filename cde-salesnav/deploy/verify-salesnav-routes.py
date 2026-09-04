#!/usr/bin/env python3
"""Guardrail: /salesnav/ must be landing, /salesnav/panel/ must be panel."""

import sys
from pathlib import Path

LANDING_MARKER = "cde-page: landing"
PANEL_MARKER = "cde-page: panel"
LANDING_TITLE = "Sales Navigator Export — CSV leads from your SN lists"
PANEL_TITLE = "My panel — Sales Navigator Export"


def _read(path):
    if not path.is_file():
        raise SystemExit(f"ERROR missing file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def check_landing(path):
    text = _read(path)
    errors = []
    if PANEL_MARKER in text or "product-salesnav-panel" in text:
        errors.append(f"{path}: looks like panel HTML (must be landing)")
    if LANDING_MARKER not in text:
        errors.append(f"{path}: missing marker {LANDING_MARKER!r}")
    if LANDING_TITLE not in text:
        errors.append(f"{path}: missing landing title")
    if "salesnav-hero" not in text:
        errors.append(f"{path}: missing salesnav-hero section")
    return errors


def check_panel(path):
    text = _read(path)
    errors = []
    if LANDING_MARKER in text or "salesnav-hero" in text:
        errors.append(f"{path}: looks like landing HTML (must be panel)")
    if PANEL_MARKER not in text:
        errors.append(f"{path}: missing marker {PANEL_MARKER!r}")
    if PANEL_TITLE not in text:
        errors.append(f"{path}: missing panel title")
    if "product-salesnav-panel" not in text:
        errors.append(f"{path}: missing product-salesnav-panel body class")
    if "panel-main" not in text:
        errors.append(f"{path}: missing panel-main section")
    return errors


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "public"
    landing = root / "salesnav" / "index.html"
    panel = root / "salesnav" / "panel" / "index.html"
    errors = check_landing(landing) + check_panel(panel)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"OK landing={landing} panel={panel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
