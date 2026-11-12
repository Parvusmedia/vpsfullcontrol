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

function eur(x: number): string {
  return `${Math.round(x * 100) / 100} €`;
}

function cpa(spend: number, conv: number): number | null {
  return conv > 0 ? Math.round((spend / conv) * 100) / 100 : null;
}

function shortCampaign(campaign: string): string {
  if (campaign.length <= 48) return campaign;
  return `${campaign.slice(0, 45)}…`;
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
    const match = String(r.match_type ?? "—");
    const label = `${kw} (${match})`;
    const camp = shortCampaign(campaign);

    if (spend >= 15 && conv === 0 && clicks >= 5) {
      out.push({
        id: id(),
        severity: "high",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions: conv,
        cpa: null,
        action: `Pausar la keyword «${kw}» [${match}] · ${eur(spend)} y ${clicks} clics sin conversiones (ventana 14 d). Si el término no encaja con la oferta, añadir negativa a nivel campaña o cuenta.`,
        detail: `Campaña ${camp}.`,
      });
    } else if (qs > 0 && qs < 5 && spend >= 8) {
      const c = cpa(spend, conv);
      out.push({
        id: id(),
        severity: "medium",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions: conv,
        cpa: c,
        action: `Mejorar QS de «${kw}» [${match}]: QS ${qs}, ${eur(spend)} · Revisar concordancia anuncio↔keyword, LP y CTR; si no mejora en 7 d, pausar la keyword.`,
        detail: c != null ? `CPA actual ${eur(c)} · ${camp}.` : `Sin conv atribuidas · ${camp}.`,
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
        action: `Restringir «${kw}» (BROAD): ${eur(spend)} sin conv. Pasar a frase/exacta o pausar; revisar términos de búsqueda y volcar irrelevantes como negativas.`,
        detail: camp,
      });
    } else if (conv >= 1 && cpa(spend, conv)! < 40) {
      const c = cpa(spend, conv)!;
      out.push({
        id: id(),
        severity: "low",
        entity: "keyword",
        campaign,
        label,
        spend,
        clicks,
        conversions: conv,
        cpa: c,
        action: `Mantener «${kw}» [${match}]: CPA ${eur(c)} (${conv.toFixed(1)} conv). Valorar subir puja ≤10 % solo tras revisar ritmo de campaña (sin superar ±20 % presupuesto).`,
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
        action: `Grupo «${name}» (${camp}): ${eur(spend)}, ${clicks} clics, 0 conv. Revisar URL final del grupo, RSA (≥1 titular alineado) y extensiones; pausar el grupo solo si tras el arreglo sigue sin conv.`,
        detail: "Entidad: ad group ENABLED en ventana 14 d.",
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
        action: `Anuncio «${short}» (${adType}, ${camp}): ${eur(spend)} sin conv. Sustituir/desactivar este RSA, probar 2 titulares + CTA nuevos y validar LP; pausar el anuncio si el grupo tiene otra RSA con conv.`,
        detail: `${clicks} clics en ventana 14 d.`,
      });
    }
  }

  const order = { high: 0, medium: 1, low: 2, info: 3 };
  out.sort((a, b) => order[a.severity] - order[b.severity] || b.spend - a.spend);
  return out.slice(0, 120);
}
