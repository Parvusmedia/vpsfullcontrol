import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { filterCampaigns, getLookbackDays, loadBrief } from "../lib/brief.js";

export default defineTool({
  description:
    "Lista campañas del brief 8k€ con tier, lookback y flags de mutación. Filtra por país, tier o clave brief.",
  effect: "read",
  inputSchema: z.object({
    tier: z.enum(["T1", "T2", "T3", "T4"]).optional(),
    pais: z.string().length(2).optional(),
    nombre_en_brief: z.string().optional(),
  }),
  async execute({ tier, pais, nombre_en_brief }) {
    const brief = loadBrief();
    const campaigns = filterCampaigns({ tier, pais, nombre_en_brief });
    return {
      meta: brief.meta,
      count: campaigns.length,
      campaigns: campaigns.map((c) => ({
        ...c,
        lookback_days: getLookbackDays(c.tier),
      })),
      excluded_from_plan: brief.excluded_from_plan,
      docs: {
        runbook: "Project store docs/google-ads-agent-runbook.md",
        cadencia: "Project store docs/google-ads-cadencia-revision.md",
      },
    };
  },
});
