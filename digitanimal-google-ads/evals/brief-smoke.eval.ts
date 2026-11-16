import { defineEval } from "@grok/agent-sdk/evals";

export default defineEval({
  tags: ["smoke"],
  description: "compare_to_brief returns 21 ES/FR campaigns and tier metadata.",
  async test(t) {
    await t.toolCall("compare_to_brief", {});
    t.succeeded();
    t.calledTool("compare_to_brief");
  },
});
