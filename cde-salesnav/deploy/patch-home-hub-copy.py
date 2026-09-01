#!/usr/bin/env python3
"""Patch companydataenrichment.com homepage hub copy (index.html + app.js)."""
import re
import sys
from pathlib import Path

DOCROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/var/www/vhosts/companydataenrichment.com/httpdocs")

INDEX_REPLACEMENTS = [
    (
        '<div class="hub-badge-row">\n          <span class="hub-badge" data-i18n="hub.badge1">Free demo</span>\n        </div>',
        '<div class="hub-badge-row">\n          <span class="hub-badge" data-i18n="hub.badge1">Free demo · Companies</span>\n          <span class="hub-badge" data-i18n="hub.badge2">From €20 · Sales Navigator</span>\n        </div>',
    ),
    (
        'data-i18n="hub.ctaCompanies">Try Companies',
        'data-i18n="hub.ctaCompanies">Enrich companies',
    ),
    (
        'data-i18n="hub.ctaSalesnav">Try Sales Navigator',
        'data-i18n="hub.ctaSalesnav">Export SN lists',
    ),
    (
        '<span data-i18n="hub.salesnav.stat">25</span>\n            <span data-i18n="hub.salesnav.statLabel">free demo leads</span>',
        '<span data-i18n="hub.salesnav.stat">120</span>\n            <span data-i18n="hub.salesnav.statLabel">credits · €20 top-up</span>',
    ),
    (
        '<li data-i18n="hub.salesnav.p2">Credits from €20</li>',
        '<li data-i18n="hub.salesnav.p2">€0.05 / lead · Basic tier</li>',
    ),
    (
        'data-i18n="hub.salesnav.cta">Export CSV',
        'data-i18n="hub.salesnav.cta">Top up &amp; export',
    ),
]

JS_REPLACEMENTS = [
    ('"hub.badge1": "Free demo",', '"hub.badge1": "Free demo · Companies",'),
    ('"hub.badge1": "Demo gratis",', '"hub.badge1": "Demo gratis · Companies",'),
    ('"hub.ctaCompanies": "Try Companies",', '"hub.ctaCompanies": "Enrich companies",'),
    ('"hub.ctaCompanies": "Probar Companies",', '"hub.ctaCompanies": "Enriquecer empresas",'),
    ('"hub.ctaSalesnav": "Try Sales Navigator",', '"hub.ctaSalesnav": "Export SN lists",'),
    ('"hub.ctaSalesnav": "Probar Sales Navigator",', '"hub.ctaSalesnav": "Exportar listas SN",'),
    ('"hub.salesnav.stat": "25",', '"hub.salesnav.stat": "120",'),
    ('"hub.salesnav.statLabel": "free demo leads",', '"hub.salesnav.statLabel": "credits · €20 top-up",'),
    ('"hub.salesnav.statLabel": "leads gratis en demo",', '"hub.salesnav.statLabel": "créditos · recarga €20",'),
    ('"hub.salesnav.p2": "Credits from €20",', '"hub.salesnav.p2": "€0.05 / lead · Basic tier",'),
    ('"hub.salesnav.p2": "Créditos desde €20",', '"hub.salesnav.p2": "€0,05 / lead · tier Basic",'),
    ('"hub.salesnav.cta": "Export CSV",', '"hub.salesnav.cta": "Top up & export",'),
    ('"hub.salesnav.cta": "Exportar CSV",', '"hub.salesnav.cta": "Recargar y exportar",'),
]

BADGE2_EN = '"hub.badge2": "From €20 · Sales Navigator",'
BADGE2_ES = '"hub.badge2": "Desde €20 · Sales Navigator",'


def patch_index(path: Path) -> bool:
    text = path.read_text()
    original = text
    for old, new in INDEX_REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text)
        return True
    return False


def ensure_badge2_i18n(js: str) -> str:
    if BADGE2_EN in js:
        return js
    js = js.replace(
        '"hub.badge1": "Free demo · Companies",',
        '"hub.badge1": "Free demo · Companies",\n    ' + BADGE2_EN,
        1,
    )
    js = js.replace(
        '"hub.badge1": "Demo gratis · Companies",',
        '"hub.badge1": "Demo gratis · Companies",\n    ' + BADGE2_ES,
        1,
    )
    return js


def patch_app_js(path: Path) -> bool:
    text = path.read_text()
    original = text
    for old, new in JS_REPLACEMENTS:
        text = text.replace(old, new)
    text = ensure_badge2_i18n(text)
    if text != original:
        path.write_text(text)
        return True
    return False


def bump_app_js_version(index_path: Path) -> bool:
    text = index_path.read_text()
    m = re.search(r'app\.js\?v=(\d+)', text)
    if not m:
        return False
    ver = int(m.group(1)) + 1
    new_text = re.sub(r'app\.js\?v=\d+', f'app.js?v={ver}', text, count=1)
    if new_text == text:
        return False
    index_path.write_text(new_text)
    return True


def main() -> None:
    idx = DOCROOT / "index.html"
    js = DOCROOT / "app.js"
    changed = False
    if idx.exists() and patch_index(idx):
        print("index.html hub copy patched")
        changed = True
    else:
        print("index.html hub copy ok")
    if js.exists() and patch_app_js(js):
        print("app.js hub copy patched")
        changed = True
    else:
        print("app.js hub copy ok")
    if changed and idx.exists() and bump_app_js_version(idx):
        print("app.js cache version bumped")


if __name__ == "__main__":
    main()
