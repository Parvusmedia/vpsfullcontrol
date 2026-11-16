import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { filterCampaigns, getLookbackDays } from "../lib/brief.js";

export default defineTool({
  description:
    "Devuelve qué consultar en Windsor MCP (queries separadas: actividad vs conversiones por acción). No llama Windsor; guía al modelo.",
  effect: "read",
  inputSchema: z.object({
    tier: z.enum(["T1", "T2", "T3", "T4"]).optional(),
    pais: z.string().length(2).optional(),
    date_from: z.string().optional(),
    date_to: z.string().optional(),
  }),
  async execute({ tier, pais, date_from, date_to }) {
    const campaigns = filterCampaigns({ tier, pais });
    const lookback =
      tier != null ? getLookbackDays(tier) : getLookbackDays("T2");

    return {
      account: "AW-846006068",
      rules: [
        "No mezclar clicks/spend con conversion_action_name en una sola query Windsor",
        "Spend: TRUNC a 2 decimales en euros",
        "Campañas ENABLED sin spend pueden no aparecer en Windsor",
        "En exports a hoja/Digitanimal, campaign suele ser nombre_en_brief; cruzar con brief JSON a campana (Ads UI)",
      ],
      suggested_windows: { lookback_days: lookback, date_from, date_to },
      queries: [
        {
          purpose: "universe",
          fields: ["campaign", "campaign_id", "campaign_status"],
          filter: "ENABLED",
        },
        {
          purpose: "activity",
          fields: ["date", "campaign", "campaign_id", "clicks", "spend"],
          campaign_names: campaigns.map((c) => c.campana),
        },
        {
          purpose: "conversions",
          fields: [
            "date",
            "campaign",
            "campaign_id",
            "conversion_action_name",
            "conversion_action_category",
            "conversions",
          ],
          lead_categories: [
            "LEAD",
            "SUBMIT_LEAD_FORM",
            "SIGNUP",
            "CONTACT",
            "QUALIFIED_LEAD",
          ],
          purchase_categories: ["PURCHASE"],
        },
      ],
    };
  },
});
