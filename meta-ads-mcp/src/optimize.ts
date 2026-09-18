export type OptimizationAction = {
  type: "pause" | "activate" | "budget_increase" | "budget_decrease";
  entity_type: "campaign" | "adset" | "ad";
  entity_id: string;
  entity_name?: string;
  reason: string;
  current_budget_cents?: number;
  proposed_budget_cents?: number;
};

export type InsightRow = {
  campaign_id?: string;
  campaign_name?: string;
  adset_id?: string;
  adset_name?: string;
  ad_id?: string;
  ad_name?: string;
  spend?: string;
  impressions?: string;
  clicks?: string;
  actions?: Array<{ action_type: string; value: string }>;
};

export function parseSpend(row: InsightRow): number {
  return Number(row.spend || 0);
}

export function countAction(row: InsightRow, types: string[]): number {
  if (!row.actions) return 0;
  let n = 0;
  for (const a of row.actions) {
    if (types.some((t) => a.action_type === t || a.action_type.startsWith(t))) {
      n += Number(a.value || 0);
    }
  }
  return n;
}

export function suggestFromInsights(
  rows: InsightRow[],
  opts: {
    level: "campaign" | "adset" | "ad";
    maxCpa?: number;
    minRoas?: number;
    minSpend?: number;
    budgetChangeMaxPct: number;
  },
): OptimizationAction[] {
  const out: OptimizationAction[] = [];
  const minSpend = opts.minSpend ?? 10;

  for (const row of rows) {
    const spend = parseSpend(row);
    if (spend < minSpend) continue;

    const leads = countAction(row, ["lead", "onsite_conversion.lead_grouped"]);
    const purchases = countAction(row, ["purchase", "offsite_conversion.fb_pixel_purchase"]);
    const conversions = leads + purchases;

    const id =
      opts.level === "campaign"
        ? row.campaign_id
        : opts.level === "adset"
          ? row.adset_id
          : row.ad_id;
    const name =
      opts.level === "campaign"
        ? row.campaign_name
        : opts.level === "adset"
          ? row.adset_name
          : row.ad_name;

    if (!id) continue;

    if (spend >= minSpend && conversions === 0) {
      out.push({
        type: "pause",
        entity_type: opts.level,
        entity_id: id,
        entity_name: name,
        reason: `Spend ${spend.toFixed(2)} with 0 leads/purchases in period`,
      });
      continue;
    }

    if (opts.maxCpa && conversions > 0) {
      const cpa = spend / conversions;
      if (cpa > opts.maxCpa) {
        out.push({
          type: "pause",
          entity_type: opts.level,
          entity_id: id,
          entity_name: name,
          reason: `CPA ${cpa.toFixed(2)} above max ${opts.maxCpa}`,
        });
      }
    }

    if (opts.minRoas && purchases > 0) {
      const roas = (purchases * 50) / spend;
      if (roas >= opts.minRoas) {
        out.push({
          type: "budget_increase",
          entity_type: opts.level,
          entity_id: id,
          entity_name: name,
          reason: `Estimated ROAS ${roas.toFixed(2)} >= ${opts.minRoas} (heuristic; confirm with your value rules)`,
        });
      }
    }
  }

  return out;
}

export function clampBudgetChange(
  currentCents: number,
  proposedCents: number,
  maxPct: number,
): number {
  if (currentCents <= 0) return proposedCents;
  const maxDelta = currentCents * (maxPct / 100);
  const delta = proposedCents - currentCents;
  if (Math.abs(delta) <= maxDelta) return proposedCents;
  return Math.round(currentCents + Math.sign(delta) * maxDelta);
}
