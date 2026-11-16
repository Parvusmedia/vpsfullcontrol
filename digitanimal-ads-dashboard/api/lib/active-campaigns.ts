export function isPlanActiveRow(row: Record<string, unknown>, now = new Date()): boolean {
  const incluir = String(row.incluir ?? "SI").toUpperCase();
  if (incluir !== "SI") return false;
  const start = parseSheetDate(row.fecha_inicio);
  const end = parseSheetDate(row.fecha_fin);
  if (start && now < start) return false;
  if (end && now > end) return false;
  return true;
}

function parseSheetDate(v: unknown): Date | null {
  if (!v) return null;
  const d = new Date(String(v));
  return Number.isNaN(d.getTime()) ? null : d;
}

export function activeBriefKeys(rows: Record<string, unknown>[]): Set<string> {
  const s = new Set<string>();
  for (const r of rows) {
    if (!isPlanActiveRow(r)) continue;
    const k = String(r.nombre_en_brief ?? "");
    if (k) s.add(k);
  }
  return s;
}

export function isPmaxBrief(brief: string): boolean {
  return brief.includes("max-rendimiento");
}
