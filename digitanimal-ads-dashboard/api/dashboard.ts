const SAMPLE = {
  updatedAt: "2026-11-12T10:00:00.000Z",
  cumplimiento: [] as Record<string, unknown>[],
  presupuesto_activacion: [] as Record<string, unknown>[],
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
    const data = await res.json();
    return Response.json({ source: "live", ...data });
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
