import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { appendChange, readChanges } from "../lib/change-log.js";
import { filterCampaigns } from "../lib/brief.js";

export default defineTool({
  description:
    "Marca un cambio como applied tras OK humano. Ejecuta mutación con herramientas Google Ads MCP (windsor verify después). Requiere change_id en estado proposed/approved.",
  effect: "write",
  needsApproval: true,
  inputSchema: z.object({
    change_id: z.string().uuid(),
    mcp_applied: z.boolean().describe("true si Google Ads MCP ya aplicó el presupuesto"),
    mcp_error: z.string().optional(),
  }),
  async execute({ change_id, mcp_applied, mcp_error }, ctx) {
    const records = await readChanges(ctx.host.files, { limit: 500 });
    const proposal = records.find((r) => r.change_id === change_id);
    if (!proposal) {
      return { ok: false, error: "change_id_not_found", change_id };
    }
    if (proposal.status === "rejected") {
      return { ok: false, error: "proposal_was_rejected", change_id };
    }

    const approvedBy =
      ctx.approvedBy?.attributes?.email ??
      ctx.approvedBy?.attributes?.user_id ??
      ctx.session?.auth?.attributes?.email ??
      "human";

    if (!mcp_applied) {
      await appendChange(ctx.host.files, {
        ...proposal,
        change_id: proposal.change_id,
        ts: new Date().toISOString(),
        status: "failed",
        approved_by: approvedBy,
        rationale: mcp_error ?? "Google Ads MCP no aplicó el cambio",
        run_id: ctx.session?.id,
      });
      return {
        ok: false,
        error: "mcp_not_applied",
        hint: "Usa herramientas del conector Google Ads MCP en la cuenta AW-846006068",
      };
    }

    const campaign = filterCampaigns({
      nombre_en_brief: proposal.nombre_en_brief ?? "",
    })[0];

    await appendChange(ctx.host.files, {
      change_id,
      ts: new Date().toISOString(),
      status: "applied",
      pais: proposal.pais,
      nombre_en_brief: proposal.nombre_en_brief,
      campana: proposal.campana ?? campaign?.campana,
      change_type: proposal.change_type,
      before: proposal.before,
      after: proposal.after,
      rationale: proposal.rationale,
      tier: proposal.tier,
      approved_by: approvedBy,
      run_id: ctx.session?.id,
    });

    return {
      ok: true,
      change_id,
      next_steps: [
        "Reconsultar Windsor en lookback de la campaña",
        "record_change status verified con windsor_snapshot",
      ],
    };
  },
});
