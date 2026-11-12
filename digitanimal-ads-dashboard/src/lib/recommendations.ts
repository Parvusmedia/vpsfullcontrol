import { countryFromBrief, num, pctDisplay, type Row } from "./metrics";
import { normalizeCumplimientoRow } from "./normalize";

export type Tier = "T1" | "T2" | "T3" | "T4";

const EXCLUDED_BRIEF = new Set([
  "gr_gps_subvencion-grecia_leads_202610",
]);

const BRAND_BRIEF = "es_generico_proteccion-marca_branding_202604";

export function tierFromDaily(daily: number): Tier {
  if (daily >= 12) return "T1";
  if (daily >= 6) return "T2";
  if (daily >= 2) return "T3";
  return "T4";
}

const REVIEW_LABEL: Record<Tier, string> = {
  T1: "Diaria (L–V)",
  T2: "Cada 2 días",
  T3: "Mar/Jue",
  T4: "Semanal (mar)",
};

export type Recommendation = {
  tier: Tier;
  review: string;
  severity: "ok" | "warn" | "alert" | "mute";
  text: string;
};

export function recommend(raw: Row): Recommendation {
  const r = normalizeCumplimientoRow(raw);
  const brief = String(r.nombre_en_brief ?? "");
  const daily = num(r.presupuesto_diario);
  const tier = tierFromDaily(daily);
  const review = REVIEW_LABEL[tier];
  const nota = String(r.nota ?? "").trim();

  if (nota) {
    return { tier, review, severity: "warn", text: nota };
  }

  if (EXCLUDED_BRIEF.has(brief)) {
    return {
      tier,
      review,
      severity: "mute",
      text: "Fuera del plan 8k€ (subvención Grecia). No ajustar presupuesto del brief.",
    };
  }

  const incluir = String(r.incluir ?? "SI").toUpperCase();
  if (incluir === "NO") {
    return {
      tier,
      review,
      severity: "mute",
      text: "Excluida del plan (incluir=NO). Solo monitorizar.",
    };
  }

  const pct = pctDisplay(r.pct_cumplimiento);
  const desvio = num(r.desvio_eur);
  const spend = num(r.spend);

  if (spend === 0 && (tier === "T1" || tier === "T2")) {
    return {
      tier,
      review,
      severity: "alert",
      text: "Spend 0 en campaña T1/T2: revisar estado ENABLED y entrega hoy.",
    };
  }

  if (pct < 80) {
    const up = Math.min(20, Math.round((80 - pct) / 2));
    let text = `Ritmo bajo (${pct.toFixed(0)} %): valorar subir presupuesto hasta +${up} % vs plan (máx. ±20 %; cooldown 48 h).`;
    if (tier === "T4") {
      text += " En T4 no tocar puja sin ventana larga.";
    }
    if (brief === BRAND_BRIEF) {
      text += " Marca ES: requiere OK humano explícito.";
    }
    return { tier, review, severity: "warn", text };
  }

  if (pct > 120) {
    const down = Math.min(20, Math.round((pct - 100) / 3));
    return {
      tier,
      review,
      severity: "warn",
      text: `Por encima del plan (${pct.toFixed(0)} %, +${desvio.toFixed(0)} €): valorar bajar presupuesto ~${down} % para volver al ritmo.`,
    };
  }

  if (Math.abs(desvio) > num(r.budget_consumido) * 0.25 && num(r.budget_consumido) > 0) {
    return {
      tier,
      review,
      severity: "warn",
      text: `Desvío > 25 % vs consumo esperado (${desvio.toFixed(0)} €): priorizar ajuste de presupuesto antes que puja.`,
    };
  }

  return {
    tier,
    review,
    severity: "ok",
    text: `Ritmo dentro de banda (${pct.toFixed(0)} %). Siguiente revisión: ${review}. Priorizar conversiones atribuidas vs all_conversions.`,
  };
}

export function countryTierLabel(raw: Row): string {
  const brief = String(raw.nombre_en_brief ?? "");
  const c = countryFromBrief(brief);
  const tier = tierFromDaily(num(normalizeCumplimientoRow(raw).presupuesto_diario));
  return `${c} · ${tier}`;
}
