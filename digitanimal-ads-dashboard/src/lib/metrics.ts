export type Row = Record<string, unknown>;

export function countryFromBrief(key: string): string {
  const m = key.match(/^([a-z]{2})_/);
  return (m?.[1] ?? "??").toUpperCase();
}

export function num(v: unknown): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string") {
    const n = parseFloat(v.replace(",", "."));
    return Number.isNaN(n) ? 0 : n;
  }
  return 0;
}

export function pctDisplay(v: unknown): number {
  const n = num(v);
  if (n > 1.5) return n;
  return n * 100;
}

export function truncEur(v: number): number {
  return Math.trunc(v * 100) / 100;
}
