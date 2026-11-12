import {
  addConversionRow,
  emptyConversionTotals,
  type ConversionTotals,
} from "./conversion-classify";
import { windsorQuery } from "./windsor-client";

export async function fetchCampaignConversionSplit(
  apiKey: string,
  dateFrom: string,
  dateTo: string
): Promise<Map<string, ConversionTotals>> {
  const rows = await windsorQuery(
    apiKey,
    [
      "campaign",
      "conversion_action_name",
      "conversion_action_category",
      "conversions",
    ],
    dateFrom,
    dateTo,
    [["campaign_status", "eq", "ENABLED"]]
  );
  const map = new Map<string, ConversionTotals>();
  for (const r of rows) {
    const campaign = String(r.campaign ?? "");
    if (!campaign) continue;
    const conv = Number(r.conversions ?? 0);
    if (conv <= 0) continue;
    const t = map.get(campaign) ?? emptyConversionTotals();
    addConversionRow(
      t,
      r.conversion_action_category,
      r.conversion_action_name,
      conv
    );
    map.set(campaign, t);
  }
  return map;
}

export function keywordSplitKey(campaign: string, keyword: string): string {
  return `${campaign}\0${keyword.trim().toLowerCase()}`;
}

export async function fetchKeywordConversionSplit(
  apiKey: string,
  dateFrom: string,
  dateTo: string
): Promise<Map<string, ConversionTotals>> {
  const rows = await windsorQuery(
    apiKey,
    [
      "campaign",
      "keyword_text",
      "conversion_action_name",
      "conversion_action_category",
      "conversions",
    ],
    dateFrom,
    dateTo,
    [["keyword_status", "eq", "ENABLED"]]
  );
  const map = new Map<string, ConversionTotals>();
  for (const r of rows) {
    const kw = String(r.keyword_text ?? "").trim();
    if (!kw) continue;
    const conv = Number(r.conversions ?? 0);
    if (conv <= 0) continue;
    const key = keywordSplitKey(String(r.campaign ?? ""), kw);
    const t = map.get(key) ?? emptyConversionTotals();
    addConversionRow(
      t,
      r.conversion_action_category,
      r.conversion_action_name,
      conv
    );
    map.set(key, t);
  }
  return map;
}
