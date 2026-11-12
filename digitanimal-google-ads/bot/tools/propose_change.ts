import { randomUUID } from "node:crypto";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import {
  appendChange,
  findCampaign,
  hoursSince,
  readChanges,
} from "../lib/change-log.js";
import { filterCampaigns, getLookbackDays } from "../lib/brief.js";

const COOLDOWN_HOURS = 48;
const BUDGET_MAX_DELTA_RATIO = 0.2;

export default defineTool({
  description:
    "Propone un cambio con validación (brief, cooldown 48h, ±20% presupuesto). Escribe status proposed en historial.",
  effect: "write",
  inputSchema: z.object({
    nombre_en_brief: z.string(),
    change_type: z.enum([
      "budget_daily",
      "status",
      "bid_strategy",
      "negative_keyword",
      "other",
    ]),
    after: z.record(z.string(), z.unknown()),
    before: z.record(z.string(), z.unknown()).optional(),
    rationale: z.string(),
    windsor_snapshot: z.record(z.string(), z.unknown()).optional(),
    bypass_cooldown: z.boolean().optional(),
  }),
  async execute(input, ctx) {
    const matches = filterCampaigns({ nombre_en_brief: input.nombre_en_brief });
    if (matches.length !== 1) {
      return { ok: false, error: "unknown_brief_key", nombre_en_brief: input.nombre_en_brief };
    }
    const campaign = matches[0];
    if (campaign.mutations_allowed === false) {
      return {
        ok: false,
        error: "mutations_not_allowed",
        campana: campaign.campana,
        notes: campaign.notes,
      };
    }

    if (input.change_type === "budget_daily" && input.after.budget_eur_daily != null) {
      const planned = campaign.presupuesto_diario_eur;
      const next = Number(input.after.budget_eur_daily);
      const delta = Math.abs(next - planned) / planned;
      if (delta > BUDGET_MAX_DELTA_RATIO) {
        return {
          ok: false,
          error: "budget_delta_exceeds_20pct",
          planned,
          proposed: next,
          max_delta_ratio: BUDGET_MAX_DELTA_RATIO,
        };
      }
    }

    const recent = await readChanges(ctx.host.files, { limit: 500 });
    const last = findCampaign(recent, input.nombre_en_brief);
    if (
      !input.bypass_cooldown &&
      input.change_type === "budget_daily" &&
      last &&
      hoursSince(last.ts) < COOLDOWN_HOURS
    ) {
      return {
        ok: false,
        error: "cooldown_active",
        hours_since_last: hoursSince(last.ts),
        last_change_id: last.change_id,
      };
    }

    const change_id = randomUUID();
    const record = {
      change_id,
      ts: new Date().toISOString(),
      status: "proposed" as const,
      pais: campaign.pais,
      nombre_en_brief: campaign.nombre_en_brief,
      campana: campaign.campana,
      change_type: input.change_type,
      before: input.before ?? { budget_eur_daily: campaign.presupuesto_diario_eur },
      after: input.after,
      rationale: input.rationale,
      tier: campaign.tier,
      lookback_days: getLookbackDays(campaign.tier),
      windsor_snapshot: input.windsor_snapshot,
      approved_by: null,
      run_id: ctx.session?.id,
    };
    const { path } = await appendChange(ctx.host.files, record);
    return {
      ok: true,
      change_id,
      path,
      message:
        "Propuesta registrada. Pide OK humano; luego apply_budget_change o Google Ads MCP.",
      record,
    };
  },
});
