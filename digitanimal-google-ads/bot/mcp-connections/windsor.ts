import { defineConnection } from "@grok/agent-sdk/connections";

export default defineConnection({
  cursorAccount: true,
  servers: ["windsor"],
  advertiseTools: true,
  optional: true,
});
