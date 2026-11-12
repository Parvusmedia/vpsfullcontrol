import { num, round2, windsorQuery } from "./windsor-client";
import { BRIEF_META, planCampaigns } from "./brief-plan";

const PLAN_KEYS = new Set(
  planCampaigns().map((c) => c.nombre_en_brief)
);

export async function fetchEnabledPlanBriefs(
  apiKey: string
): Promise<Set<string>> {
  const rows = await windsorQuery(
    apiKey,
    ["campaign", "campaign_status"],
    BRIEF_META.period_start,
    BRIEF_META.period_end,
    [["campaign_status", "eq", "ENABLED"]]
  );
  const enabled = new Set<string>();
  for (const r of rows) {
    const brief = String(r.campaign ?? "");
    if (PLAN_KEYS.has(brief) && String(r.campaign_status) === "ENABLED") {
      enabled.add(brief);
    }
  }
  return enabled;
}

export async function fetchActivationMetrics(apiKey: string): Promise<
  Map<
    string,
    {
      campaign_name: string;
      spend: number;
      conversions: number;
      clicks: number;
      cpa: number | null;
    }
  >
> {
  const rows = await windsorQuery(
    apiKey,
    [
      "campaign",
      "campaign_name",
      "campaign_status",
      "spend",
      "clicks",
      "conversions",
      "cost_per_conversion",
    ],
    BRIEF_META.period_start,
    BRIEF_META.period_end,
    [["campaign_status", "eq", "ENABLED"]]
  );
  const map = new Map<
    string,
    {
      campaign_name: string;
      spend: number;
      conversions: number;
      clicks: number;
      cpa: number | null;
    }
  >();
  for (const r of rows) {
    const brief = String(r.campaign ?? "");
    if (!PLAN_KEYS.has(brief)) continue;
    const platformName = String(r.campaign_name ?? r.campaign ?? brief);
    const conversions = num(r.conversions);
    const spend = round2(num(r.spend));
    const clicks = num(r.clicks);
    let cpa = num(r.cost_per_conversion);
    if (!cpa && conversions > 0) cpa = spend / conversions;
    map.set(brief, {
      campaign_name: platformName,
      spend,
      conversions: round2(conversions),
      clicks: Math.round(clicks),
      cpa: conversions > 0 ? round2(cpa) : null,
    });
  }
  return map;
}
