import type { HostFilesApi } from "@grok/agent-sdk";

export type ChangeStatus =
  | "proposed"
  | "approved"
  | "rejected"
  | "applied"
  | "failed"
  | "verified"
  | "revert";

export type ChangeRecord = {
  change_id: string;
  ts: string;
  status: ChangeStatus;
  pais?: string;
  nombre_en_brief?: string;
  campana?: string;
  change_type?: string;
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  rationale?: string;
  tier?: string;
  lookback_days?: number;
  windsor_snapshot?: Record<string, unknown>;
  approved_by?: string | null;
  run_id?: string;
  ref_change_id?: string;
  rejection_reason?: string;
};

function monthPath(ts: string): string {
  const d = new Date(ts);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `changes/${y}-${m}.jsonl`;
}

export async function appendChange(
  files: HostFilesApi,
  record: ChangeRecord
): Promise<{ path: string }> {
  const path = monthPath(record.ts);
  const line = JSON.stringify(record) + "\n";
  const existing = (await files.read(path).catch(() => null)) ?? "";
  await files.write(path, existing + line);
  return { path };
}

export async function readChanges(
  files: HostFilesApi,
  opts: { path?: string; limit?: number }
): Promise<ChangeRecord[]> {
  const path = opts.path ?? monthPath(new Date().toISOString());
  const raw = await files.read(path).catch(() => "");
  if (!raw.trim()) return [];
  const lines = raw.trim().split("\n");
  const records = lines.map((l) => JSON.parse(l) as ChangeRecord);
  const limit = opts.limit ?? 200;
  return records.slice(-limit);
}

export function findCampaign(
  records: ChangeRecord[],
  nombre_en_brief: string
): ChangeRecord | undefined {
  for (let i = records.length - 1; i >= 0; i--) {
    const r = records[i];
    if (
      r.nombre_en_brief === nombre_en_brief &&
      (r.status === "applied" || r.status === "proposed" || r.status === "approved")
    ) {
      return r;
    }
  }
  return undefined;
}

export function hoursSince(iso: string): number {
  return (Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60);
}
