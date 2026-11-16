/** Clasifica conversiones Google Ads en registro (CPL) vs compra (CPA). */

export type ConversionBucket = "lead" | "purchase" | "other";

export function classifyConversionAction(
  category: unknown,
  actionName: unknown
): ConversionBucket {
  const cat = String(category ?? "").toUpperCase();
  const name = String(actionName ?? "").toLowerCase();

  if (
    cat.includes("PURCHASE") ||
    cat.includes("BEGIN_CHECKOUT") ||
    /compra|purchase|pedido|checkout/.test(name)
  ) {
    return "purchase";
  }

  if (
    cat.includes("LEAD") ||
    cat.includes("SUBMIT") ||
    cat.includes("CONTACT") ||
    cat.includes("SIGNUP") ||
    cat.includes("QUALIFIED") ||
    cat.includes("PHONE_CALL") ||
    /contacto|formulario|lead|captura|whatsapp|llamada|registro|submit/.test(name)
  ) {
    return "lead";
  }

  return "other";
}

export type ConversionTotals = {
  lead: number;
  purchase: number;
  other: number;
  total: number;
};

export function emptyConversionTotals(): ConversionTotals {
  return { lead: 0, purchase: 0, other: 0, total: 0 };
}

export function addConversionRow(
  totals: ConversionTotals,
  category: unknown,
  actionName: unknown,
  conversions: number
): void {
  if (conversions <= 0) return;
  const bucket = classifyConversionAction(category, actionName);
  totals[bucket] += conversions;
  totals.total += conversions;
}

export function costPerLead(spend: number, lead: number): number | null {
  return lead > 0 ? Math.round((spend / lead) * 100) / 100 : null;
}

export function costPerPurchase(spend: number, purchase: number): number | null {
  return purchase > 0 ? Math.round((spend / purchase) * 100) / 100 : null;
}

/** Etiqueta de coste principal según objetivo del brief. */
export function primaryCostKind(objetivo: string): "cpl" | "cpa" {
  if (objetivo === "ventas") return "cpa";
  return "cpl";
}
