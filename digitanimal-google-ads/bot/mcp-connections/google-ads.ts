import { defineConnection } from "@grok/agent-sdk/connections";

/** Mutaciones en cuenta Google Ads (presupuesto, estado, etc.). Conectar en Cursor → Tools & MCP. */
export default defineConnection({
  cursorAccount: true,
  servers: ["Google Ads", "google-ads", "GoogleAds"],
  advertiseTools: true,
  optional: true,
});
