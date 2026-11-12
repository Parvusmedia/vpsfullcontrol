type Row = Record<string, unknown>;

export type Insight = {
  id: string;
  severity: "high" | "medium" | "low" | "info";
  entity: "campaign" | "ad_group" | "keyword" | "ad";
  campaign: string;
  label: string;
  spend: number;
  clicks: number;
  conversions: number;
  cpa: number | null;
  action: string;
  detail: string;
};

function n(v: unknown): number {
  if (typeof v === "number") return v;
  if (typeof v === "string") return parseFloat(v) || 0;
  return 0;
}

function cpa(spend: number, conv: number): number | null {
  return conv > 0 ? Math.round((spend / conv) * 100) / 100 : null;
}

export function buildInsights(input: {
  adGroups: Row[];
  keywords: Row[];
  ads: Row[];
  activeBriefs: Set<string>;
}): Insight[] {
  const out: Insight[] = [];
  let seq = 0;
  const id = () => `i-${++seq}`;

  for (const r of input.keywords) {
    const campaign = String(r.campaign ?? "");
    if (!input.activeBriefs.has(campaign)) continue;
    if (String(r.keyword_status ?? "ENABLED") !== "ENABLED") continue;
    const kw = String(r.keyword_text ?? "");
    if (!kw) continue;
    const spend = n(r.spend);
    const clicks = n(r.clicks);
    const conv = n(r.conversions);
    const qs = n(r.quality_score);
    const match = String(r.match_type ?? "");

    if (spend >= 15 && conv === 0 && clicks >= 5) {
      out.push({
        id: id(),
        severity: "high",
        entity: "keyword",
        campaign,
        label: `${kw} (${match})`,
        spend,
        clicks,
        conversions: conv,
        cpa: null,
        action: "Pausar o añadir negativa",
        detail: "Gasto alto sin conversión atribuida en ventana.",
      });
    } else if (qs > 0 && qs < 5 && spend >= 8) {
      out.push({
        id: id(),
        severity: "medium",
        entity: "keyword",
        campaign,
        label: `${kw} (${match})`,
        spend,
        clicks,
        conversions: conv,
        cpa: cpa(spend, conv),
        action: "Mejorar anuncio/landing o pausar",
        detail: `Quality Score bajo (${qs}).`,
      });
    } else if (match === "BROAD" && spend >= 20 && conv === 0) {
      out.push({
        id: id(),
        severity: "medium",
        entity: "keyword",
        campaign,
        label: `${kw} (BROAD)`,
        spend,
        clicks,
        conversions: conv,
        cpa: null,
        action: "Restringir concordancia o negativas",
        detail: "Broad con gasto sin conversión.",
      });
    } else if (conv >= 1 && cpa(spend, conv)! < 40) {
      out.push({
        id: id(),
        severity: "low",
        entity: "keyword",
        campaign,
        label: `${kw} (${match})`,
        spend,
        clicks,
        conversions: conv,
        cpa: cpa(spend, conv),
        action: "Mantener / escalar con control",
        detail: "Keyword eficiente en la ventana.",
      });
    }
  }

  for (const r of input.adGroups) {
    const campaign = String(r.campaign ?? "");
    if (!input.activeBriefs.has(campaign)) continue;
    const st = r.ad_group_status;
    if (st != null && String(st) !== "ENABLED") continue;
    const name = String(r.ad_group_name ?? r.ad_group ?? "—");
    const spend = n(r.spend);
    const clicks = n(r.clicks);
    const conv = n(r.conversions);
    if (spend < 10) continue;

    if (conv === 0 && clicks >= 12 && spend >= 20) {
      out.push({
        id: id(),
        severity: "high",
        entity: "ad_group",
        campaign,
        label: name,
        spend,
        clicks,
        conversions: 0,
        cpa: null,
        action: "Revisar anuncios/URLs o pausar grupo",
        detail: "Grupo activo con clics y sin conversiones.",
      });
    }
  }

  for (const r of input.ads) {
    const campaign = String(r.campaign ?? "");
    if (!input.activeBriefs.has(campaign)) continue;
    const adName = String(r.ad_name ?? "");
    if (!adName) continue;
    const spend = n(r.spend);
    const clicks = n(r.clicks);
    const conv = n(r.conversions);
    const short = adName.length > 80 ? `${adName.slice(0, 77)}…` : adName;

    if (spend >= 25 && conv === 0 && clicks >= 15) {
      out.push({
        id: id(),
        severity: "medium",
        entity: "ad",
        campaign,
        label: short,
        spend,
        clicks,
        conversions: 0,
        cpa: null,
        action: "Rotar creatividades RSA / revisar extensiones",
        detail: `Tipo ${String(r.ad_type ?? "—")}.`,
      });
    }
  }

  const order = { high: 0, medium: 1, low: 2, info: 3 };
  out.sort((a, b) => order[a.severity] - order[b.severity] || b.spend - a.spend);
  return out.slice(0, 120);
}
