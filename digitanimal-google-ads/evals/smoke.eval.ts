import { defineEval } from "@grok/agent-sdk/evals";

export default defineEval({
  tags: ["smoke"],
  description: "compare_to_brief lists activation campaigns.",
  async test(t) {
    await t.toolCall("compare_to_brief", { pais: "ES" });
    t.succeeded();
    t.calledTool("compare_to_brief");
  },
});
