#!/bin/bash
# Deploy Sales Navigator section to companydataenrichment.com
set -euo pipefail

REMOTE="parvus-vps"
ROOT="/opt/apps/companydataenrichment/public"
LOCAL="/workspace/cde-salesnav/public"

echo "==> Copy new files"
scp -r "$LOCAL/salesnav" "$REMOTE:$ROOT/"
scp "$LOCAL/api/_unipile.php" "$REMOTE:$ROOT/api/"
scp "$LOCAL/api/salesnav-export.php" "$REMOTE:$ROOT/api/"

echo "==> Patch .htaccess to protect _unipile.php"
ssh "$REMOTE" "grep -q '_unipile' $ROOT/api/.htaccess || sed -i 's/_bootstrap/_bootstrap|_unipile/' $ROOT/api/.htaccess"

echo "==> Patch contact.php volume labels"
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
path = Path('$ROOT/api/contact.php')
text = path.read_text()
needle = \"    '50k-200k' => '50,000 – 200,000',\\n\";
insert = needle + \"\"\"    '500' => 'Up to 500 leads/month',
    '1k-3k' => '1,000 – 3,000 leads/month',
    '3k-10k' => '3,000 – 10,000 leads/month',
    '10k+' => '10,000+ leads/month',
\"\"\"
if \"'1k-3k'\" not in text:
    if needle not in text:
        raise SystemExit('contact.php anchor not found')
    text = text.replace(needle, insert)
    path.write_text(text)
    print('contact.php patched')
else:
    print('contact.php already patched')
PY"

echo "==> Patch index.html header nav"
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
path = Path('$ROOT/index.html')
text = path.read_text()
old = '''  <header class=\"top\">
    <a class=\"brand\" href=\"/\">CompanyDataEnrichment</a>
    <div class=\"lang-switch\" role=\"group\" aria-label=\"Language\">'''
new = '''  <header class=\"top\">
    <a class=\"brand\" href=\"/\">CompanyDataEnrichment</a>
    <nav class=\"site-nav\" aria-label=\"Products\">
      <a href=\"/\" class=\"is-active\" aria-current=\"page\" data-i18n=\"nav.companies\">Companies</a>
      <a href=\"/salesnav/\" data-i18n=\"nav.salesnav\">Sales Navigator</a>
    </nav>
    <div class=\"top-actions\">
      <div class=\"lang-switch\" role=\"group\" aria-label=\"Language\">'''
if old not in text:
    if 'site-nav' in text:
        print('index.html nav already patched')
    else:
        raise SystemExit('index.html header anchor not found')
else:
    text = text.replace(old, new)
    text = text.replace('    </div>\n  </header>', '    </div>\n    </div>\n  </header>', 1)
    path.write_text(text)
    print('index.html header patched')
PY"

echo "==> Patch index.html footer + stylesheet version"
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
path = Path('$ROOT/index.html')
text = path.read_text()
if '/salesnav/' not in text.split('foot-links')[1] if 'foot-links' in text else '':
    text = text.replace(
        '<div class=\"foot-links\">\n      <a href=\"https://www.parvusmedia.com/\"',
        '<div class=\"foot-links\">\n      <a href=\"/salesnav/\">Sales Navigator</a>\n      <a href=\"https://www.parvusmedia.com/\"'
    )
text = text.replace('styles.css?v=23', 'styles.css?v=24')
path.write_text(text)
print('index.html footer/css updated')
PY"

echo "==> Append shared nav CSS to styles.css"
ssh "$REMOTE" "grep -q '.site-nav' $ROOT/styles.css || cat >> $ROOT/styles.css <<'CSS'

/* Shared product nav (Companies | Sales Navigator) */
.site-nav {
  display: inline-flex;
  gap: 0.15rem;
  margin-left: auto;
  margin-right: 1rem;
}
.site-nav a {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.82rem;
  letter-spacing: -0.01em;
  color: var(--ink-soft);
  text-decoration: none;
  padding: 0.45rem 0.65rem;
  border: 1.5px solid transparent;
}
.site-nav a:hover {
  color: var(--ink);
  border-color: var(--line);
  background: rgba(255, 255, 255, 0.5);
}
.site-nav a.is-active {
  color: var(--teal-deep);
  border-color: var(--teal);
  background: rgba(31, 111, 106, 0.1);
}
.top-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
CSS"

echo "==> Patch sitemap.xml"
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
path = Path('$ROOT/sitemap.xml')
text = path.read_text()
if '/salesnav/' not in text:
    insert = '''  <url>
    <loc>https://companydataenrichment.com/salesnav/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.90</priority>
  </url>
'''
    text = text.replace('</urlset>', insert + '</urlset>')
    path.write_text(text)
print('sitemap updated')
PY"

echo "==> Patch app.js nav i18n keys"
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
path = Path('$ROOT/app.js')
text = path.read_text()
if 'nav.companies' not in text:
    text = text.replace(
        '  en: {',
        '  en: {\n    \"nav.companies\": \"Companies\",\n    \"nav.salesnav\": \"Sales Navigator\",',
        1,
    )
    text = text.replace(
        '  es: {',
        '  es: {\n    \"nav.companies\": \"Empresas\",\n    \"nav.salesnav\": \"Sales Navigator\",',
        1,
    )
    path.write_text(text)
print('app.js i18n updated')
PY"

echo "==> Done"
