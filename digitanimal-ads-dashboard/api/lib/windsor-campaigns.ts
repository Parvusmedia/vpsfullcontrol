import { costPerLead, costPerPurchase } from "./conversion-classify";
import {
  fetchCampaignConversionSplit,
  type ConversionActionLine,
} from "./windsor-conversions";
import { num, round2, windsorQuery } from "./windsor-client";
import { BRIEF_META, planCampaigns } from "./brief-plan";

const PLAN_KEYS = new Set(
  planCampaigns().map((c) => c.nombre_en_brief)
);

export async function fetchEnabledPlanBriefs(
  apiKey: string,
  dateFrom: string,
  dateTo: string
): Promise<Set<string>> {
  const rows = await windsorQuery(
    apiKey,
    ["campaign", "campaign_status"],
    dateFrom,
    dateTo,
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

export type ActivationMetrics = {
  campaign_name: string;
  spend: number;
  conversions: number;
  conversions_lead: number;
  conversions_purchase: number;
  conversions_other: number;
  clicks: number;
  cpl: number | null;
  cpa: number | null;
  conversion_actions: ConversionActionLine[];
};

export async function fetchActivationMetrics(
  apiKey: string,
  dateFrom: string,
  dateTo: string
): Promise<Map<string, ActivationMetrics>> {
  const [rows, split] = await Promise.all([
    windsorQuery(
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
      dateFrom,
      dateTo,
      [["campaign_status", "eq", "ENABLED"]]
    ),
    fetchCampaignConversionSplit(apiKey, dateFrom, dateTo),
  ]);
  const map = new Map<string, ActivationMetrics>();
  for (const r of rows) {
    const brief = String(r.campaign ?? "");
    if (!PLAN_KEYS.has(brief)) continue;
    const platformName = String(r.campaign_name ?? r.campaign ?? brief);
    const conversions = num(r.conversions);
    const spend = round2(num(r.spend));
    const clicks = num(r.clicks);
    const convSplit = split.get(brief);
    const conversions_lead = round2(convSplit?.lead ?? 0);
    const conversions_purchase = round2(convSplit?.purchase ?? 0);
    const conversions_other = round2(convSplit?.other ?? 0);
    const totalSplit =
      conversions_lead + conversions_purchase + conversions_other;
    const conversionsTotal =
      totalSplit > 0 ? round2(totalSplit) : round2(conversions);
    map.set(brief, {
      campaign_name: platformName,
      spend,
      conversions: conversionsTotal,
      conversions_lead,
      conversions_purchase,
      conversions_other,
      clicks: Math.round(clicks),
      cpl: costPerLead(spend, conversions_lead),
      cpa: costPerPurchase(spend, conversions_purchase),
      conversion_actions: convSplit?.actions ?? [],
    });
  }
  return map;
}
