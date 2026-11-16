import { num, type Row } from "./metrics";

/** Alinea nombres de columna de la hoja con lo que usa el panel. */
export function normalizeCumplimientoRow(raw: Row): Row & {
  budget_consumido: number;
  presupuesto_diario: number;
} {
  const budget =
    num(raw.budget_consumido_eur) ||
    num(raw.budget_consumido) ||
    num(raw.budget_plan_eur);
  const daily =
    num(raw.presupuesto_diario_eur) ||
    num(raw.presupuesto_diario) ||
    num(raw["presupuesto_diario"]);
  return {
    ...raw,
    budget_consumido: budget,
    presupuesto_diario: daily,
  };
}
