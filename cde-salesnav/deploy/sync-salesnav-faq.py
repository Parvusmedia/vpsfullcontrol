#!/usr/bin/env python3
"""Sync Sales Nav FAQ fragment into landing + panel (single source of truth)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = ROOT / "public" / "salesnav" / "_faq-section.fragment.html"
TARGETS = [
    (ROOT / "public" / "salesnav" / "index.html", 'class="strip faq-section" id="faq"'),
    (ROOT / "public" / "salesnav" / "panel" / "index.html", 'class="strip faq-section panel-faq" id="faq"'),
]

BEGIN = "<!-- SN_FAQ_FRAGMENT -->"
END = "<!-- /SN_FAQ_FRAGMENT -->"


def inject(path: Path, section_open: str) -> None:
    text = path.read_text(encoding="utf-8")
    body = FRAGMENT.read_text(encoding="utf-8").rstrip() + "\n"
    block = f"    <section {section_open}>\n{BEGIN}\n{body}    {END}\n    </section>"
    pattern = re.compile(
        r"    <section " + re.escape(section_open) + r">.*?</section>",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(f"FAQ section not found in {path}")
    new_text = pattern.sub(block, text, count=1)
    if new_text == text:
        print(f"FAQ already synced -> {path.relative_to(ROOT)}")
        return
    path.write_text(new_text, encoding="utf-8")
    print(f"synced FAQ -> {path.relative_to(ROOT)}")


def main() -> int:
    if not FRAGMENT.is_file():
        print(f"missing fragment: {FRAGMENT}", file=sys.stderr)
        return 1
    for path, section_open in TARGETS:
        if not path.is_file():
            print(f"missing target: {path}", file=sys.stderr)
            return 1
        inject(path, section_open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
