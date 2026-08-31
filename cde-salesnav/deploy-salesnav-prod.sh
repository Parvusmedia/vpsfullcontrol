#!/bin/bash
# Deploy Sales Navigator section to production (82.223.3.205 via nextconvers-vps)
set -euo pipefail

REMOTE="parvus-vps"
PROD="nextconvers-vps"
DOCROOT="/var/www/vhosts/companydataenrichment.com/httpdocs"
PRIVATE="/var/www/vhosts/companydataenrichment.com/private/cde"
LOCAL="/workspace/cde-salesnav/public"
STAGING="/opt/apps/companydataenrichment/public"

echo "==> Stage files on parvus-vps"
scp -r "$LOCAL/salesnav" "$REMOTE:$STAGING/"
scp "$LOCAL/api/_unipile.php" "$LOCAL/api/salesnav-export.php" "$REMOTE:$STAGING/api/"

echo "==> Apply patches on parvus-vps staging (if not already)"
ssh "$REMOTE" "bash /opt/apps/companydataenrichment/../..//workspace/cde-salesnav/deploy-salesnav.sh 2>/dev/null || true"

# Re-run patch logic inline on staging
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
root = Path('$STAGING')
# contact.php patch on staging only if needed - skip, production has own contact.php
# Ensure htaccess
ht = root / 'api' / '.htaccess'
text = ht.read_text()
if '_unipile' not in text:
    ht.write_text(text.replace('_bootstrap', '_bootstrap|_unipile'))
print('staging ready')
PY"

echo "==> Sync Unipile env to production (from linkedinreport on parvus-vps)"
ssh "$REMOTE" "grep '^UNIPILE_' /etc/linkedinreport/app.env | ssh $PROD \"install -d -m 700 $PRIVATE && cat > $PRIVATE/unipile.env && chmod 600 $PRIVATE/unipile.env\""

echo "==> Rsync public site to production httpdocs"
ssh "$REMOTE" "rsync -avz --exclude 'apify.env' --exclude 'unipile.env' \
  $STAGING/ $PROD:$DOCROOT/"

echo "==> Patch production contact.php volume labels"
ssh "$REMOTE" "ssh $PROD python3 - <<'PY'
from pathlib import Path
path = Path('$DOCROOT/api/contact.php')
text = path.read_text()
needle = \"    '50k-200k' => '50,000 – 200,000',\\n\"
insert = needle + \"\"\"    '500' => 'Up to 500 leads/month',
    '1k-3k' => '1,000 – 3,000 leads/month',
    '3k-10k' => '3,000 – 10,000 leads/month',
    '10k+' => '10,000+ leads/month',
\"\"\"
if \"'1k-3k'\" not in text and needle in text:
    path.write_text(text.replace(needle, insert))
    print('contact.php patched')
else:
    print('contact.php ok')
PY"

echo "==> Patch production index.html nav + footer"
ssh "$REMOTE" "ssh $PROD python3 - <<'PY'
from pathlib import Path
path = Path('$DOCROOT/index.html')
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
if old in text:
    text = text.replace(old, new)
    text = text.replace('    </div>\n  </header>', '    </div>\n    </div>\n  </header>', 1)
if '/salesnav/' not in text.split('foot-links')[1]:
    text = text.replace(
        '<div class=\"foot-links\">\n      <a href=\"https://www.parvusmedia.com/\"',
        '<div class=\"foot-links\">\n      <a href=\"/salesnav/\">Sales Navigator</a>\n      <a href=\"https://www.parvusmedia.com/\"'
    )
text = text.replace('styles.css?v=23', 'styles.css?v=24')
path.write_text(text)
print('index.html updated')
PY"

echo "==> Append nav CSS on production if missing"
ssh "$REMOTE" "ssh $PROD \"grep -q '.site-nav' $DOCROOT/styles.css 2>/dev/null || cat >> $DOCROOT/styles.css <<'CSS'

.site-nav{display:inline-flex;gap:.15rem;margin-left:auto;margin-right:1rem}
.site-nav a{font-family:var(--font-display);font-weight:700;font-size:.82rem;color:var(--ink-soft);text-decoration:none;padding:.45rem .65rem;border:1.5px solid transparent}
.site-nav a:hover{color:var(--ink);border-color:var(--line);background:rgba(255,255,255,.5)}
.site-nav a.is-active{color:var(--teal-deep);border-color:var(--teal);background:rgba(31,111,106,.1)}
.top-actions{display:flex;align-items:center;gap:.75rem}
@media (max-width:900px){.site-nav{display:none}}
CSS\""

echo "==> Update sitemap + app.js i18n on production"
ssh "$REMOTE" "ssh $PROD python3 - <<'PY'
from pathlib import Path
sm = Path('$DOCROOT/sitemap.xml')
t = sm.read_text()
if '/salesnav/' not in t:
    sm.write_text(t.replace('</urlset>', '''  <url><loc>https://companydataenrichment.com/salesnav/</loc><changefreq>weekly</changefreq><priority>0.90</priority></url>\n</urlset>'''))
js = Path('$DOCROOT/app.js')
j = js.read_text()
if 'nav.companies' not in j:
    j = j.replace('  en: {', '  en: {\n    \"nav.companies\": \"Companies\",\n    \"nav.salesnav\": \"Sales Navigator\",', 1)
    j = j.replace('  es: {', '  es: {\n    \"nav.companies\": \"Empresas\",\n    \"nav.salesnav\": \"Sales Navigator\",', 1)
    js.write_text(j)
print('sitemap/app.js ok')
PY"

echo "==> Set ownership on production"
ssh "$REMOTE" "ssh $PROD \"chown -R companydataenrichment:psacln $DOCROOT/salesnav $DOCROOT/api/_unipile.php $DOCROOT/api/salesnav-export.php 2>/dev/null || true\""

echo "==> Done — production deploy complete"
