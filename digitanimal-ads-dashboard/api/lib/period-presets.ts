import { BRIEF_META, daysElapsedInPlan } from "./brief-plan";

export type PeriodPresetId = "plan" | "last7" | "last14" | "last28";

export type ResolvedPeriod = {
  id: PeriodPresetId;
  label: string;
  from: string;
  to: string;
  /** Días del tramo (para presupuesto esperado = €/día × días). */
  budgetDays: number;
  pacingMode: "plan" | "rolling";
  recommendationNote: string;
};

export const PERIOD_PRESET_OPTIONS: {
  id: PeriodPresetId;
  label: string;
}[] = [
  { id: "plan", label: "Plan 8k€ (acumulado)" },
  { id: "last7", label: "Últimos 7 días" },
  { id: "last14", label: "Últimos 14 días" },
  { id: "last28", label: "Últimos 28 días" },
];

const PLAN_START = BRIEF_META.period_start;
const PLAN_END = BRIEF_META.period_end;

function fmt(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function parseYmd(s: string): Date {
  return new Date(`${s}T12:00:00Z`);
}

function clipToPlan(from: string, to: string): { from: string; to: string } {
  const f = parseYmd(from);
  const t = parseYmd(to);
  const ps = parseYmd(PLAN_START);
  const pe = parseYmd(PLAN_END);
  const cf = f < ps ? ps : f;
  const ct = t > pe ? pe : t;
  if (cf > ct) return { from: PLAN_START, to: PLAN_START };
  return { from: fmt(cf), to: fmt(ct) };
}

function inclusiveDays(from: string, to: string): number {
  const a = parseYmd(from).getTime();
  const b = parseYmd(to).getTime();
  if (b < a) return 0;
  return Math.ceil((b - a) / 86400000) + 1;
}

function rollingWindow(days: number, now = new Date()): { from: string; to: string } {
  const to = new Date(now);
  const from = new Date(now);
  from.setUTCDate(from.getUTCDate() - (days - 1));
  return clipToPlan(fmt(from), fmt(to));
}

export function parsePresetId(raw: string | null | undefined): PeriodPresetId {
  const id = (raw ?? "plan").toLowerCase();
  if (id === "last7" || id === "last14" || id === "last28" || id === "plan") {
    return id;
  }
  return "plan";
}

export function resolvePeriod(
  preset: PeriodPresetId,
  now = new Date()
): ResolvedPeriod {
  if (preset === "plan") {
    const dias = daysElapsedInPlan(now);
    const endCap = now > parseYmd(PLAN_END) ? PLAN_END : fmt(now);
    const from = PLAN_START;
    const to = endCap > PLAN_END ? PLAN_END : endCap;
    return {
      id: "plan",
      label: "Plan 8k€ (acumulado)",
      from,
      to,
      budgetDays: dias,
      pacingMode: "plan",
      recommendationNote:
        "Ritmo y recomendaciones vs presupuesto acumulado del plan (oct–dic).",
    };
  }

  const days = preset === "last7" ? 7 : preset === "last14" ? 14 : 28;
  const { from, to } = rollingWindow(days, now);
  const budgetDays = inclusiveDays(from, to);
  const label =
    preset === "last7"
      ? "Últimos 7 días"
      : preset === "last14"
        ? "Últimos 14 días"
        : "Últimos 28 días";

  return {
    id: preset,
    label,
    from,
    to,
    budgetDays,
    pacingMode: "rolling",
    recommendationNote: `Ritmo y recomendaciones vs €/día × ${budgetDays} d del tramo (${from} → ${to}), recortado al plan.`,
  };
}