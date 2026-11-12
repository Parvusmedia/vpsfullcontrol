import { BRIEF_META, buildCumplimientoRows, presupuestoActivacionRows } from "./lib/brief-plan";
import { fetchDeepAnalysis } from "./lib/windsor-deep";
import {
  fetchActivationMetrics,
  fetchEnabledPlanBriefs,
} from "./lib/windsor-campaigns";

function analysisWindow(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(from.getDate() - 13);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { from: fmt(from), to: fmt(to) };
}

export async function GET(): Promise<Response> {
  const windsorKey = process.env.WINDSOR_API_KEY;
  if (!windsorKey) {
    return Response.json({
      source: "sample",
      message: "Fuente: Windsor API. Añade WINDSOR_API_KEY en Secrets del panel.",
      updatedAt: new Date().toISOString(),
      cumplimiento: [],
      presupuesto_activacion: presupuestoActivacionRows(),
      metrics_period: { from: BRIEF_META.period_start, to: BRIEF_META.period_end },
    });
  }

  try {
    const [enabledBriefs, metrics] = await Promise.all([
      fetchEnabledPlanBriefs(windsorKey),
      fetchActivationMetrics(windsorKey),
    ]);

    const cumplimiento = buildCumplimientoRows(enabledBriefs, metrics);
    const win = analysisWindow();
    const deep_analysis = await fetchDeepAnalysis(
      windsorKey,
      enabledBriefs,
      win.from,
      win.to
    );

    return Response.json({
      source: "live",
      data_source: "windsor",
      updatedAt: new Date().toISOString(),
      cumplimiento,
      presupuesto_activacion: presupuestoActivacionRows(),
      metrics_period: { from: BRIEF_META.period_start, to: BRIEF_META.period_end },
      analysis_window: win,
      deep_analysis,
      metrics_note:
        "Solo campañas ENABLED del brief 8k€ (Windsor). Ritmo vs brief JSON; profundidad últimos 14 días.",
    });
  } catch (e) {
    return Response.json(
      {
        source: "error",
        message: e instanceof Error ? e.message : "Windsor fetch failed",
        cumplimiento: [],
      },
      { status: 502 }
    );
  }
}
