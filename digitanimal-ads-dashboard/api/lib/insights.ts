type Row = Record<string, unknown>;

import {
  costPerLead,
  costPerPurchase,
  type ConversionTotals,
} from "./conversion-classify";
import { keywordSplitKey } from "./windsor-conversions";

export type Insight = {
  id: string;
  severity: "high" | "medium" | "low" | "info";
  entity: "campaign" | "ad_group" | "keyword" | "ad";
  campaign: string;
  label: string;
  spend: number;
  clicks: number;
  conversions: number;
  conversions_lead: number;
  conversions_purchase: number;
  cpl: number | null;
  cpa: number | null;
  action: string;
  detail: string;
};

function n(v: unknown): number {
  if (typeof v === "number") return v;
  if (typeof v === "string") return parseFloat(v) || 0;
  return 0;
}

function eur(x: number): string {
  return `${Math.round(x * 100) / 100} €`;
}

function convCosts(
  spend: number,
  lead: number,
  purchase: number
): { cpl: number | null; cpa: number | null } {
  return {
    cpl: costPerLead(spend, lead),
    cpa: costPerPurchase(spend, purchase),
  };
}

function insightConv(
  entity: Insight["entity"],
  campaign: string,
  keywordText: string | null,
  totalFromRow: number,
  keywordConvSplit?: Map<string, ConversionTotals>
): { lead: number; purchase: number; total: number } {
  if (entity === "keyword" && keywordText && keywordConvSplit) {
    const split = keywordConvSplit.get(keywordSplitKey(campaign, keywordText));
    if (split && split.total > 0) {
      return {
        lead: split.lead,
        purchase: split.purchase,
        total: split.total,
      };
    }
  }
  return { lead: totalFromRow, purchase: 0, total: totalFromRow };
}

function shortCampaign(campaign: string): string {
  if (campaign.length <= 48) return campaign;
  return `${campaign.slice(0, 45)}…`;
}

function pushInsight(
  out: Insight[],
  id: () => string,
  base: Omit<Insight, "id" | "conversions_lead" | "conversions_purchase" | "cpl" | "cpa" | "conversions"> & {
    conversions_total: number;
    lead: number;
    purchase: number;
  }
) {
  const costs = convCosts(base.spend, base.lead, base.purchase);
  out.push({
    id: id(),
    severity: base.severity,
    entity: base.entity,
    campaign: base.campaign,
    label: base.label,
    spend: base.spend,
    clicks: base.clicks,
    conversions: base.conversions_total,
    conversions_lead: base.lead,
    conversions_purchase: base.purchase,
    cpl: costs.cpl,
    cpa: costs.cpa,
    action: base.action,
    detail: base.detail,
  });
}

export function buildInsights(input: {
  adGroups: Row[];
  keywords: Row[];
  ads: Row[];
  activeBriefs: Set<string>;
  keywordConvSplit?: Map<string, ConversionTotals>;
  campaignObjetivo?: Map<string, string>;
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
    const convRow = n(r.conversions);
    const conv = insightConv(
      "keyword",
      campaign,
      kw,
      convRow,
      input.keywordConvSplit
    );
    const qs = n(r.quality_score);
    const match = String(r.match_type ?? "—");
    const label = `${kw} (${match})`;
    const camp = shortCampaign(campaign);
    const objetivo = input.campaignObjetivo?.get(campaign) ?? "ventas";
    const primaryZero =
      objetivo === "ventas"
        ? conv.purchase + conv.lead === 0
        : conv.lead === 0;

    if (spend >= 15 && primaryZero && clicks >= 5) {
      pushInsight(out, id, {
        severity: "high",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions_total: conv.total,
        lead: conv.lead,
        purchase: conv.purchase,
        action: `Pausar la keyword «${kw}» [${match}] · ${eur(spend)} y ${clicks} clics sin ${objetivo === "ventas" ? "registros ni compras" : "registros"} (14 d). Si no encaja, negativa en campaña/cuenta.`,
        detail: `Campaña ${camp}.`,
      });
    } else if (qs > 0 && qs < 5 && spend >= 8) {
      const costs = convCosts(spend, conv.lead, conv.purchase);
      const costLine =
        costs.cpl != null
          ? `CPL ${eur(costs.cpl)}`
          : costs.cpa != null
            ? `CPA ${eur(costs.cpa)}`
            : "Sin coste/conv.";
      pushInsight(out, id, {
        severity: "medium",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions_total: conv.total,
        lead: conv.lead,
        purchase: conv.purchase,
        action: `Mejorar QS de «${kw}» [${match}]: QS ${qs}, ${eur(spend)} · Revisar anuncio↔keyword, LP y CTR; si no mejora en 7 d, pausar.`,
        detail: `${costLine} · ${camp}.`,
      });
    } else if (match === "BROAD" && spend >= 20 && primaryZero) {
      pushInsight(out, id, {
        severity: "medium",
        entity: "keyword",
        campaign,
        label: `${kw} (BROAD)`,
        spend,
        clicks,
        conversions_total: conv.total,
        lead: conv.lead,
        purchase: conv.purchase,
        action: `Restringir «${kw}» (BROAD): ${eur(spend)} sin conv. útiles. Frase/exacta o pausar; negativas desde términos de búsqueda.`,
        detail: camp,
      });
    } else if (conv.purchase >= 1 && convCosts(spend, conv.lead, conv.purchase).cpa! < 80) {
      const c = convCosts(spend, conv.lead, conv.purchase).cpa!;
      pushInsight(out, id, {
        severity: "low",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions_total: conv.total,
        lead: conv.lead,
        purchase: conv.purchase,
        action: `Mantener «${kw}» [${match}]: CPA ${eur(c)} (${conv.purchase.toFixed(1)} compras). Subir puja ≤10 % solo si el ritmo de campaña lo permite.`,
        detail: camp,
      });
    } else if (conv.lead >= 1 && convCosts(spend, conv.lead, conv.purchase).cpl! < 45) {
      const c = convCosts(spend, conv.lead, conv.purchase).cpl!;
      pushInsight(out, id, {
        severity: "low",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions_total: conv.total,
        lead: conv.lead,
        purchase: conv.purchase,
        action: `Mantener «${kw}» [${match}]: CPL ${eur(c)} (${conv.lead.toFixed(1)} registros). Escalar con control de presupuesto (±20 %).`,
        detail: camp,
      });
    }
  }

  for (const r of input.adGroups) {
    const campaign = String(r.campaign ?? "");
    if (!input.activeBriefs.has(campaign)) continue;
    const st = r.ad_group_status;
    if (st != null && String(st) !== "ENABLED") continue;
    const rawName = String(r.ad_group_name ?? r.ad_group ?? "").trim();
    const camp = shortCampaign(campaign);
    const name =
      rawName && rawName !== "—"
        ? rawName
        : `Grupo (sin nombre en Windsor) · ${camp}`;
    const spend = n(r.spend);
    const clicks = n(r.clicks);
    const conv = n(r.conversions);
    if (spend < 10) continue;

    if (conv === 0 && clicks >= 12 && spend >= 20) {
      pushInsight(out, id, {
        severity: "high",
        entity: "ad_group",
        campaign,
        label: name,
        spend,
        clicks,
        conversions_total: 0,
        lead: 0,
        purchase: 0,
        action: `Grupo «${name}» (${camp}): ${eur(spend)}, ${clicks} clics, 0 registros/compras. Revisar URL, RSA y extensiones; pausar si sigue en 0 tras arreglo.`,
        detail: "Ventana 14 d · ad group ENABLED.",
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
    const adType = String(r.ad_type ?? "RSA");

    if (spend >= 25 && conv === 0 && clicks >= 15) {
      const camp = shortCampaign(campaign);
      pushInsight(out, id, {
        severity: "medium",
        entity: "ad",
        campaign,
        label: short,
        spend,
        clicks,
        conversions_total: 0,
        lead: 0,
        purchase: 0,
        action: `Anuncio «${short}» (${adType}, ${camp}): ${eur(spend)} sin conv. Rotar RSA/CTA y LP; pausar si otra RSA del grupo convierte.`,
        detail: `${clicks} clics · ventana 14 d.`,
      });
    }
  }

  const order = { high: 0, medium: 1, low: 2, info: 3 };
  out.sort((a, b) => order[a.severity] - order[b.severity] || b.spend - a.spend);
  return out.slice(0, 120);
}
