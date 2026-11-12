const ACCOUNT = "529-032-5835";

export async function windsorQuery(
  apiKey: string,
  fields: string[],
  dateFrom: string,
  dateTo: string,
  filter?: unknown[]
): Promise<Record<string, unknown>[]> {
  const params = new URLSearchParams({
    api_key: apiKey,
    fields: fields.join(","),
    date_from: dateFrom,
    date_to: dateTo,
    select_accounts: ACCOUNT,
  });
  if (filter?.length) {
    params.set("filter", JSON.stringify(filter));
  }
  const res = await fetch(
    `https://connectors.windsor.ai/google_ads?${params.toString()}`
  );
  if (!res.ok) throw new Error(`Windsor HTTP ${res.status}`);
  const body = (await res.json()) as {
    data?: Record<string, unknown>[];
    error?: unknown;
  };
  if (body.error) throw new Error("Windsor API error");
  return body.data ?? [];
}

export function num(v: unknown): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string") {
    const n = parseFloat(v);
    return Number.isNaN(n) ? 0 : n;
  }
  return 0;
}

export function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
