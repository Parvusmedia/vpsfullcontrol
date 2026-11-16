import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { readChanges } from "../lib/change-log.js";

export default defineTool({
  description:
    "Lee el historial de cambios JSONL (mes actual u path explícito). Filtra en la respuesta por país o campaña.",
  effect: "read",
  inputSchema: z.object({
    path: z.string().optional(),
    limit: z.number().int().min(1).max(500).optional(),
    pais: z.string().optional(),
    nombre_en_brief: z.string().optional(),
    status: z.string().optional(),
  }),
  async execute({ path, limit, pais, nombre_en_brief, status }, ctx) {
    let records = await readChanges(ctx.host.files, { path, limit });
    if (pais) records = records.filter((r) => r.pais === pais);
    if (nombre_en_brief)
      records = records.filter((r) => r.nombre_en_brief === nombre_en_brief);
    if (status) records = records.filter((r) => r.status === status);
    return { count: records.length, records };
  },
});
