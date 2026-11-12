import { buildInsights } from "./insights";
import { isPmaxBrief } from "./active-campaigns";
import { windsorQuery } from "./windsor-client";

export type DeepAnalysis = {
  window: { from: string; to: string };
  scope: string;
  active_campaign_count: number;
  insights: ReturnType<typeof buildInsights>;
  ad_groups: Record<string, unknown>[];
  keywords: Record<string, unknown>[];
  ads: Record<string, unknown>[];
  pmax_notes: { campaign: string; note: string }[];
};

export async function fetchDeepAnalysis(
  apiKey: string,
  activeBriefs: Set<string>,
  dateFrom: string,
  dateTo: string
): Promise<DeepAnalysis> {
  const baseFilter = [["campaign_status", "eq", "ENABLED"]] as unknown[][];

  const [adGroups, keywords, ads] = await Promise.all([
    windsorQuery(
      apiKey,
      [
        "campaign",
        "ad_group_name",
        "ad_group_status",
        "spend",
        "clicks",
        "conversions",
        "cost_per_conversion",
      ],
      dateFrom,
      dateTo,
      [...baseFilter, ["spend", "gt", 1]]
    ),
    windsorQuery(
      apiKey,
      [
        "campaign",
        "keyword_text",
        "match_type",
        "keyword_status",
        "quality_score",
        "spend",
        "clicks",
        "conversions",
      ],
      dateFrom,
      dateTo,
      [
        ...baseFilter,
        ["keyword_status", "eq", "ENABLED"],
        ["spend", "gt", 2],
      ]
    ),
    windsorQuery(
      apiKey,
      [
        "campaign",
        "ad_name",
        "ad_type",
        "ad_status",
        "spend",
        "clicks",
        "conversions",
      ],
      dateFrom,
      dateTo,
      [...baseFilter, ["spend", "gt", 5]]
    ),
  ]);

  const inPlan = (campaign: string) => activeBriefs.has(campaign);

  const ad_groups = adGroups
    .filter((r) => inPlan(String(r.campaign ?? "")))
    .slice(0, 80);
  const keywords = keywords
    .filter((r) => inPlan(String(r.campaign ?? "")))
    .slice(0, 150);
  const ads = ads.filter((r) => inPlan(String(r.campaign ?? ""))).slice(0, 80);

  const pmax_notes = [...activeBriefs]
    .filter(isPmaxBrief)
    .map((campaign) => ({
      campaign,
      note: "Performance Max: sin keywords; revisar asset groups, search terms y señales de conversión.",
    }));

  const insights = buildInsights({
    adGroups: ad_groups,
    keywords,
    ads,
    activeBriefs,
  });

  return {
    window: { from: dateFrom, to: dateTo },
    scope:
      "Brief 8k€ ∩ Windsor ENABLED; ad groups, keywords y anuncios ENABLED (sin hoja).",
    active_campaign_count: activeBriefs.size,
    insights,
    ad_groups,
    keywords,
    ads,
    pmax_notes,
  };
}
