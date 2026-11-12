import { fetchWindsorByBrief, mergeWindsorIntoCumplimiento } from "./lib/windsor";

const SAMPLE = {
  updatedAt: "2026-11-12T10:00:00.000Z",
  cumplimiento: [] as Record<string, unknown>[],
  presupuesto_activacion: [] as Record<string, unknown>[],
  metrics_period: { from: "2026-10-01", to: "2026-12-06" },
};

export async function GET(): Promise<Response> {
  const url = process.env.DIGITANIMAL_SHEETS_JSON_URL;
  if (!url) {
    return Response.json({
      source: "sample",
      message:
        "Datos de muestra. Añade el secreto DIGITANIMAL_SHEETS_JSON_URL (URL del Apps Script).",
      ...SAMPLE,
    });
  }
  try {
    const res = await fetch(url);
    if (!res.ok) {
      return Response.json(
        { source: "error", status: res.status, ...SAMPLE },
        { status: 502 }
      );
    }
    const data = (await res.json()) as Record<string, unknown>;
    const notes: string[] = [];
    const windsorKey = process.env.WINDSOR_API_KEY;
    let cumplimiento = (data.cumplimiento as Record<string, unknown>[]) ?? [];

    if (windsorKey) {
      try {
        const byBrief = await fetchWindsorByBrief(windsorKey);
        cumplimiento = mergeWindsorIntoCumplimiento(cumplimiento, byBrief);
      } catch {
        notes.push(
          "No se pudieron cargar conversiones Windsor (revisa WINDSOR_API_KEY)."
        );
      }
    } else {
      notes.push(
        "Conversiones: añade WINDSOR_API_KEY en Secrets del panel (Windsor → API key)."
      );
    }

    return Response.json({
      source: "live",
      ...data,
      cumplimiento,
      metrics_period: SAMPLE.metrics_period,
      metrics_note:
        "Conversiones y CPA: Windsor, acciones incluidas en optimización (periodo activación 8k€).",
      ...(notes.length ? { message: notes.join(" ") } : {}),
    });
  } catch (e) {
    return Response.json(
      {
        source: "error",
        message: e instanceof Error ? e.message : "fetch failed",
        ...SAMPLE,
      },
      { status: 502 }
    );
  }
}
