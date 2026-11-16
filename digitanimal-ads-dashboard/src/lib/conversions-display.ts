/** Texto para conversiones atribuidas (Google Ads puede devolver decimales). */

export function formatAttributedConversions(value: number): string {
  if (value <= 0) return "—";
  const frac = Math.abs(value - Math.round(value)) > 0.001;
  return frac ? value.toFixed(2) : value.toFixed(1);
}

export const ATTRIBUTED_CONV_TITLE =
  "Conversiones atribuidas por Google Ads (p. ej. DDA): no son conteos enteros de pedidos/formularios.";

export const PURCHASE_COL_TITLE =
  "Suma de acciones tipo PURCHASE/compra en Windsor (GA4 checkout, purchase event…), con atribución parcial.";

export const REG_COL_TITLE =
  "Suma de acciones contacto/formulario/lead (SUBMIT_LEAD_FORM, contacto_*, etc.), con atribución parcial.";
