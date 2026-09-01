#!/usr/bin/env python3
"""Extend PHP session GC lifetime for Sales Navigator panel auth."""
from __future__ import annotations

import sys
from pathlib import Path

DOCROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/var/www/vhosts/companydataenrichment.com/httpdocs')
bootstrap = DOCROOT / 'api' / '_bootstrap.php'

if not bootstrap.exists():
    print(f'missing {bootstrap}')
    sys.exit(1)

text = bootstrap.read_text()
needle = "    if (session_status() === PHP_SESSION_ACTIVE) {\n        return;\n    }\n    session_name('cde_sess');"
insert = """    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    ini_set('session.gc_maxlifetime', '2592000');
    session_name('cde_sess');"""

if 'session.gc_maxlifetime' in text:
    print(f'session lifetime ok {bootstrap}')
elif needle in text:
    bootstrap.write_text(text.replace(needle, insert, 1))
    print(f'patched {bootstrap}')
else:
    print(f'could not patch {bootstrap}')
    sys.exit(1)
