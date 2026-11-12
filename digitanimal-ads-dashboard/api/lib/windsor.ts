const CONNECTOR = "google_ads";
const ACCOUNT = "529-032-5835";
const PERIOD_FROM = "2026-10-01";
const PERIOD_TO = "2026-12-06";

export type WindsorMetrics = {
  conversions: number;
  clicks: number;
  spend: number;
  cost_per_conversion: number | null;
};

export async function fetchWindsorByBrief(
  apiKey: string
): Promise<Map<string, WindsorMetrics>> {
  const params = new URLSearchParams({
    api_key: apiKey,
    fields: "campaign,conversions,spend,clicks,cost_per_conversion",
    date_from: PERIOD_FROM,
    date_to: PERIOD_TO,
    select_accounts: ACCOUNT,
  });
  const res = await fetch(
    `https://connectors.windsor.ai/${CONNECTOR}?${params.toString()}`
  );
  if (!res.ok) {
    throw new Error(`Windsor HTTP ${res.status}`);
  }
  const body = (await res.json()) as {
    data?: Array<Record<string, unknown>>;
    error?: unknown;
  };
  if (body.error) {
    throw new Error("Windsor error");
  }
  const map = new Map<string, WindsorMetrics>();
  for (const row of body.data ?? []) {
    const brief = String(row.campaign ?? "");
    if (!brief) continue;
    const conversions = num(row.conversions);
    const spend = num(row.spend);
    const clicks = num(row.clicks);
    let cpa = num(row.cost_per_conversion);
    if (!cpa && conversions > 0) {
      cpa = spend / conversions;
    }
    map.set(brief, {
      conversions,
      clicks,
      spend,
      cost_per_conversion: conversions > 0 ? cpa : null,
    });
  }
  return map;
}

function num(v: unknown): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string") {
    const n = parseFloat(v);
    return Number.isNaN(n) ? 0 : n;
  }
  return 0;
}

export function mergeWindsorIntoCumplimiento(
  rows: Record<string, unknown>[],
  windsor: Map<string, WindsorMetrics>
): Record<string, unknown>[] {
  return rows.map((r) => {
    const brief = String(r.nombre_en_brief ?? "");
    const m = windsor.get(brief);
    if (!m) {
      return { ...r, conversions: 0, clicks: 0, cost_per_conversion: null };
    }
    return {
      ...r,
      conversions: round2(m.conversions),
      clicks: Math.round(m.clicks),
      cost_per_conversion:
        m.cost_per_conversion != null ? round2(m.cost_per_conversion) : null,
      windsor_spend: round2(m.spend),
    };
  });
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
