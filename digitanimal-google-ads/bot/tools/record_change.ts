import { randomUUID } from "node:crypto";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { appendChange, type ChangeRecord, type ChangeStatus } from "../lib/change-log.js";
import { loadBrief } from "../lib/brief.js";

const statusSchema = z.enum([
  "proposed",
  "approved",
  "rejected",
  "applied",
  "failed",
  "verified",
  "revert",
]);

export default defineTool({
  description:
    "Append-only: registra un evento en el historial de cambios (JSONL en host.files).",
  effect: "write",
  inputSchema: z.object({
    change_id: z.string().uuid().optional(),
    status: statusSchema,
    pais: z.string().optional(),
    nombre_en_brief: z.string().optional(),
    campana: z.string().optional(),
    change_type: z.string().optional(),
    before: z.record(z.string(), z.unknown()).optional(),
    after: z.record(z.string(), z.unknown()).optional(),
    rationale: z.string().optional(),
    tier: z.string().optional(),
    lookback_days: z.number().int().optional(),
    windsor_snapshot: z.record(z.string(), z.unknown()).optional(),
    approved_by: z.string().nullable().optional(),
    ref_change_id: z.string().uuid().optional(),
    rejection_reason: z.string().optional(),
  }),
  async execute(input, ctx) {
    const brief = loadBrief();
    if (input.nombre_en_brief) {
      const excluded = brief.excluded_from_plan.some(
        (e) => e.nombre_en_brief === input.nombre_en_brief
      );
      if (
        excluded &&
        (input.status === "applied" || input.status === "approved")
      ) {
        return {
          ok: false,
          error: "campaign_excluded_from_plan",
          nombre_en_brief: input.nombre_en_brief,
        };
      }
    }

    const record: ChangeRecord = {
      change_id: input.change_id ?? randomUUID(),
      ts: new Date().toISOString(),
      status: input.status as ChangeStatus,
      pais: input.pais,
      nombre_en_brief: input.nombre_en_brief,
      campana: input.campana,
      change_type: input.change_type,
      before: input.before,
      after: input.after,
      rationale: input.rationale,
      tier: input.tier,
      lookback_days: input.lookback_days,
      windsor_snapshot: input.windsor_snapshot,
      approved_by: input.approved_by ?? null,
      run_id: ctx.session?.id,
      ref_change_id: input.ref_change_id,
      rejection_reason: input.rejection_reason,
    };

    const { path } = await appendChange(ctx.host.files, record);
    return { ok: true, path, record };
  },
});
