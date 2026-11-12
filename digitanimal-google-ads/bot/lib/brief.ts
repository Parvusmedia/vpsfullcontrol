import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export type BriefCampaign = {
  pais: string;
  campana: string;
  nombre_en_brief: string;
  presupuesto_diario_eur: number;
  objetivo?: string;
  modalidad?: string;
  producto?: string;
  tier: string;
  mutations_allowed?: boolean;
  notes?: string;
};

export type BriefFile = {
  meta: {
    period_start: string;
    period_end: string;
    timezone: string;
  };
  tier_rules: Record<string, { lookback_days: number; review: string }>;
  campaigns: BriefCampaign[];
  excluded_from_plan: Array<{ nombre_en_brief: string; mutations_allowed: boolean }>;
};

const here = dirname(fileURLToPath(import.meta.url));

let cached: BriefFile | null = null;

export function loadBrief(): BriefFile {
  if (!cached) {
    const raw = readFileSync(join(here, "brief-campaigns.json"), "utf8");
    cached = JSON.parse(raw) as BriefFile;
  }
  return cached;
}

export function truncSpendEur(value: number): number {
  return Math.trunc(value * 100) / 100;
}

export function filterCampaigns(opts: {
  tier?: string;
  pais?: string;
  nombre_en_brief?: string;
}): BriefCampaign[] {
  const brief = loadBrief();
  return brief.campaigns.filter((c) => {
    if (opts.tier && c.tier !== opts.tier) return false;
    if (opts.pais && c.pais !== opts.pais) return false;
    if (opts.nombre_en_brief && c.nombre_en_brief !== opts.nombre_en_brief) return false;
    return true;
  });
}

export function getLookbackDays(tier: string): number {
  const brief = loadBrief();
  return brief.tier_rules[tier]?.lookback_days ?? 14;
}
