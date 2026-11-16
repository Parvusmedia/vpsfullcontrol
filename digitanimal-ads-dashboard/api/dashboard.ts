import { BRIEF_META, buildCumplimientoRows, presupuestoActivacionRows } from "./lib/brief-plan";
import {
  dashboardCacheKey,
  getDashboardCache,
  setDashboardCache,
} from "./lib/dashboard-cache";
import { fetchDeepAnalysis } from "./lib/windsor-deep";
import {
  fetchActivationMetrics,
  fetchEnabledPlanBriefs,
} from "./lib/windsor-campaigns";
import {
  parsePresetId,
  PERIOD_PRESET_OPTIONS,
  resolvePeriod,
} from "./lib/period-presets";

export async function GET(request: Request): Promise<Response> {
  const windsorKey = process.env.WINDSOR_API_KEY;
  const preset = parsePresetId(new URL(request.url).searchParams.get("preset"));
  const period = resolvePeriod(preset);

  if (!windsorKey) {
    return Response.json({
      source: "sample",
      message: "Fuente: Windsor API. Añade WINDSOR_API_KEY en Secrets del panel.",
      updatedAt: new Date().toISOString(),
      period_preset: preset,
      period_label: period.label,
      period_options: PERIOD_PRESET_OPTIONS,
      cumplimiento: [],
      presupuesto_activacion: presupuestoActivacionRows(),
      metrics_period: { from: period.from, to: period.to },
    });
  }

  const cacheKey = dashboardCacheKey(preset);
  const cached = getDashboardCache(cacheKey);
  if (cached) {
    return new Response(cached, {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Dashboard-Cache": "hit",
      },
    });
  }

  try {
    const [enabledBriefs, metrics] = await Promise.all([
      fetchEnabledPlanBriefs(windsorKey, period.from, period.to),
      fetchActivationMetrics(windsorKey, period.from, period.to),
    ]);

    const cumplimiento = buildCumplimientoRows(enabledBriefs, metrics, {
      from: period.from,
      to: period.to,
      budgetDays: period.budgetDays,
    });

    const deep_analysis = await fetchDeepAnalysis(
      windsorKey,
      enabledBriefs,
      period.from,
      period.to
    );

    const body = {
      source: "live",
      data_source: "windsor",
      updatedAt: new Date().toISOString(),
      period_preset: preset,
      period_label: period.label,
      period_options: PERIOD_PRESET_OPTIONS,
      pacing_mode: period.pacingMode,
      recommendation_context: period.recommendationNote,
      cumplimiento,
      presupuesto_activacion: presupuestoActivacionRows(),
      metrics_period: { from: period.from, to: period.to },
      plan_bounds: { from: BRIEF_META.period_start, to: BRIEF_META.period_end },
      analysis_window: { from: period.from, to: period.to },
      deep_analysis,
      metrics_note: `${period.label} (${period.from} → ${period.to}). CPL/CPA por acción de conversión. ${period.recommendationNote}`,
    };

    const json = JSON.stringify(body);
    setDashboardCache(cacheKey, json);

    return new Response(json, {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Dashboard-Cache": "miss",
      },
    });
  } catch (e) {
    return Response.json(
      {
        source: "error",
        message: e instanceof Error ? e.message : "Windsor fetch failed",
        period_preset: preset,
        cumplimiento: [],
      },
      { status: 502 }
    );
  }
}