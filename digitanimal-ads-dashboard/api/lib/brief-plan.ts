import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const brief = JSON.parse(
  readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "brief-campaigns.json"),
    "utf8"
  )
);

type BriefCampaign = {
  pais: string;
  campana: string;
  nombre_en_brief: string;
  presupuesto_diario_eur: number;
  tier: string;
  objetivo?: string;
  mutations_allowed?: boolean;
};

const EXCLUDED = new Set(
  (brief.excluded_from_plan as { nombre_en_brief: string }[]).map(
    (e) => e.nombre_en_brief
  )
);

export const BRIEF_META = brief.meta as {
  period_start: string;
  period_end: string;
  period_days: number;
  total_eur: number;
};

export function planCampaigns(): BriefCampaign[] {
  return (brief.campaigns as BriefCampaign[]).filter(
    (c) => !EXCLUDED.has(c.nombre_en_brief)
  );
}

export function daysElapsedInPlan(now = new Date()): number {
  const start = new Date(BRIEF_META.period_start);
  const end = new Date(BRIEF_META.period_end);
  const cap = now > end ? end : now;
  if (cap < start) return 0;
  return Math.ceil((cap.getTime() - start.getTime()) / 86400000) + 1;
}

export function buildCumplimientoRows(
  enabledBriefs: Set<string>,
  windsorSpend: Map<
    string,
    { spend: number; conversions: number; clicks: number; cpa: number | null }
  >
): Record<string, unknown>[] {
  const dias = daysElapsedInPlan();
  const rows: Record<string, unknown>[] = [];

  for (const c of planCampaigns()) {
    if (!enabledBriefs.has(c.nombre_en_brief)) continue;
    const m = windsorSpend.get(c.nombre_en_brief) ?? {
      spend: 0,
      conversions: 0,
      clicks: 0,
      cpa: null,
    };
    const budget = Math.round(c.presupuesto_diario_eur * dias * 100) / 100;
    const spend = m.spend;
    const pct = budget > 0 ? spend / budget : 0;
    rows.push({
      nombre_en_brief: c.nombre_en_brief,
      campana: c.campana,
      pais: c.pais,
      tier: c.tier,
      objetivo: c.objetivo,
      presupuesto_diario_eur: c.presupuesto_diario_eur,
      fecha_inicio: BRIEF_META.period_start,
      fecha_fin: BRIEF_META.period_end,
      dias,
      spend,
      budget_consumido_eur: budget,
      pct_cumplimiento: pct,
      desvio_eur: Math.round((spend - budget) * 100) / 100,
      conversions: m.conversions,
      clicks: m.clicks,
      cost_per_conversion: m.cpa,
      campaign_status: "ENABLED",
      incluir: "SI",
    });
  }
  return rows;
}

export function presupuestoActivacionRows(): Record<string, unknown>[] {
  return planCampaigns().map((c) => ({
    pais: c.pais,
    campana: c.campana,
    nombre_en_brief: c.nombre_en_brief,
    presupuesto_diario_eur: c.presupuesto_diario_eur,
    tier: c.tier,
    objetivo: c.objetivo,
  }));
}
