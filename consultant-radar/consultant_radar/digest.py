from __future__ import annotations

from typing import Any, Iterable


def render_digest(rows: Iterable[dict[str, Any]], *, title: str = "Consultant Radar") -> str:
    items = list(rows)
    lines = [f"# {title}", "", f"{len(items)} ofertas coincidentes.", ""]
    current = None
    for row in items:
        company = row.get("company_name") or row.get("company_id") or "—"
        if company != current:
            current = company
            lines.append(f"## {company}")
            lines.append("")
        location = row.get("location") or "—"
        keywords = ", ".join(row.get("matched_keywords") or []) or "—"
        url = row.get("url") or ""
        posted = row.get("posted_at") or ""
        extra = f" · {posted}" if posted else ""
        lines.append(f"- **{row.get('title', '').strip()}** — {location}{extra}")
        if url:
            lines.append(f"  {url}")
        lines.append(f"  keywords: {keywords}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
