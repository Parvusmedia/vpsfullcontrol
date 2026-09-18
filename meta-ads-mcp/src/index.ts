#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { loadConfig } from "./config.js";
import { formatGraphError, GraphClient } from "./graph.js";
import {
  clampBudgetChange,
  suggestFromInsights,
  type InsightRow,
} from "./optimize.js";
import { readFileSync } from "node:fs";

function loadDotEnv(): void {
  try {
    const path = new URL("../.env", import.meta.url);
    const raw = readFileSync(path, "utf8");
    for (const line of raw.split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#")) continue;
      const eq = t.indexOf("=");
      if (eq < 0) continue;
      const key = t.slice(0, eq).trim();
      let val = t.slice(eq + 1).trim();
      if (
        (val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))
      ) {
        val = val.slice(1, -1);
      }
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {
    /* no local .env */
  }
}

loadDotEnv();

const config = loadConfig();
const graph = new GraphClient(config);

const server = new McpServer({
  name: "meta-ads-mcp",
  version: "1.0.0",
});

function jsonText(data: unknown): { content: Array<{ type: "text"; text: string }> } {
  return {
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
  };
}

function errText(e: unknown): { content: Array<{ type: "text"; text: string }>; isError?: true } {
  return {
    content: [{ type: "text", text: formatGraphError(e) }],
    isError: true,
  };
}

server.tool(
  "meta_ads_account_info",
  "Ad account metadata: currency, timezone, name, account status.",
  {},
  async () => {
    try {
      const data = await graph.getWithRetry(config.adAccountId, {
        fields:
          "id,name,account_status,currency,timezone_name,amount_spent,balance,spend_cap,funding_source_details",
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_campaigns",
  "List campaigns on the configured ad account.",
  {
    limit: z.number().int().min(1).max(100).optional().default(25),
    effective_status: z
      .array(z.string())
      .optional()
      .describe("e.g. ACTIVE, PAUSED"),
    name_contains: z.string().optional(),
  },
  async ({ limit, effective_status, name_contains }) => {
    try {
      const params: Record<string, string> = {
        fields: "id,name,status,effective_status,objective,daily_budget,lifetime_budget",
        limit: String(limit),
      };
      if (effective_status?.length) {
        params.filtering = JSON.stringify([
          {
            field: "effective_status",
            operator: "IN",
            value: effective_status,
          },
        ]);
      }
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        graph.adAccountPath("campaigns"),
        params,
      );
      let rows = data.data || [];
      if (name_contains) {
        const q = name_contains.toLowerCase();
        rows = rows.filter(
          (r) =>
            String((r as { name?: string }).name || "")
              .toLowerCase()
              .includes(q),
        );
      }
      return jsonText({ data: rows });
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_get_campaign",
  "Get one campaign by ID.",
  { campaign_id: z.string() },
  async ({ campaign_id }) => {
    try {
      const data = await graph.getWithRetry(campaign_id, {
        fields:
          "id,name,status,effective_status,objective,special_ad_categories,daily_budget,lifetime_budget",
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_adsets",
  "List ad sets for a campaign.",
  {
    campaign_id: z.string(),
    limit: z.number().int().min(1).max(100).optional().default(25),
  },
  async ({ campaign_id, limit }) => {
    try {
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        `${campaign_id}/adsets`,
        {
          fields:
            "id,name,status,effective_status,daily_budget,lifetime_budget,optimization_goal,promoted_object,targeting",
          limit: String(limit),
        },
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_ads",
  "List ads for an ad set.",
  {
    adset_id: z.string(),
    limit: z.number().int().min(1).max(100).optional().default(25),
  },
  async ({ adset_id, limit }) => {
    try {
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        `${adset_id}/ads`,
        {
          fields: "id,name,status,effective_status,creative",
          limit: String(limit),
        },
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_pages",
  "Pages promotable from this ad account (for leads and ad identity).",
  { limit: z.number().int().min(1).max(100).optional().default(50) },
  async ({ limit }) => {
    try {
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        graph.adAccountPath("promote_pages"),
        { fields: "id,name,link", limit: String(limit) },
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_pixels",
  "Pixels owned by this ad account.",
  { limit: z.number().int().min(1).max(100).optional().default(50) },
  async ({ limit }) => {
    try {
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        graph.adAccountPath("adspixels"),
        { fields: "id,name", limit: String(limit) },
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_pixel_events",
  "Stats for a pixel (recent activity / event counts).",
  {
    pixel_id: z.string(),
  },
  async ({ pixel_id }) => {
    try {
      const data = await graph.getWithRetry(pixel_id, {
        fields: "id,name,last_fired_time,is_created_by_business",
      });
      const stats = await graph.getWithRetry(`${pixel_id}/stats`, {
        aggregation: "event",
      });
      return jsonText({ pixel: data, stats });
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_list_leadgen_forms",
  "Instant lead forms for a Facebook Page.",
  {
    page_id: z.string(),
    limit: z.number().int().min(1).max(100).optional().default(25),
  },
  async ({ page_id, limit }) => {
    try {
      const data = await graph.getWithRetry<{ data: unknown[] }>(
        `${page_id}/leadgen_forms`,
        { fields: "id,name,status,leads_count", limit: String(limit) },
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_insights",
  "Performance insights at campaign, adset, or ad level.",
  {
    level: z.enum(["campaign", "adset", "ad"]).default("campaign"),
    date_preset: z
      .enum([
        "today",
        "yesterday",
        "last_7d",
        "last_14d",
        "last_30d",
        "this_month",
      ])
      .default("last_7d"),
    campaign_id: z.string().optional(),
    adset_id: z.string().optional(),
    limit: z.number().int().min(1).max(100).optional().default(25),
  },
  async ({ level, date_preset, campaign_id, adset_id, limit }) => {
    try {
      let path = graph.adAccountPath("insights");
      const params: Record<string, string> = {
        level,
        date_preset,
        fields:
          "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,spend,impressions,clicks,ctr,cpc,actions,cost_per_action_type",
        limit: String(limit),
      };
      if (campaign_id) path = `${campaign_id}/insights`;
      if (adset_id) path = `${adset_id}/insights`;
      const data = await graph.getWithRetry<{ data: InsightRow[] }>(path, params);
      const rows = (data.data || []).map((row) => {
        const spend = Number(row.spend || 0);
        const leads = sumActions(row, ["lead", "onsite_conversion.lead_grouped"]);
        const purchases = sumActions(row, [
          "purchase",
          "offsite_conversion.fb_pixel_purchase",
        ]);
        const conv = leads + purchases;
        return {
          ...row,
          derived: {
            leads,
            purchases,
            conversions: conv,
            cpa: conv > 0 ? spend / conv : null,
          },
        };
      });
      return jsonText({ data: rows });
    } catch (e) {
      return errText(e);
    }
  },
);

function sumActions(row: InsightRow, types: string[]): number {
  if (!row.actions) return 0;
  let n = 0;
  for (const a of row.actions) {
    if (types.some((t) => a.action_type === t || a.action_type.startsWith(t))) {
      n += Number(a.value || 0);
    }
  }
  return n;
}

server.tool(
  "meta_ads_create_campaign",
  "Create a campaign (default PAUSED). Requires confirmed=true after user approval.",
  {
    name: z.string(),
    objective: z
      .string()
      .describe("e.g. OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC"),
    special_ad_categories: z.array(z.string()).optional().default([]),
    status: z.enum(["PAUSED", "ACTIVE"]).optional().default("PAUSED"),
    allow_active_on_create: z.boolean().optional().default(false),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    let status = args.status;
    if (status === "ACTIVE" && !args.allow_active_on_create) {
      status = "PAUSED";
    }
    try {
      const data = await graph.post(graph.adAccountPath("campaigns"), {
        name: args.name,
        objective: args.objective,
        status,
        special_ad_categories: JSON.stringify(args.special_ad_categories ?? []),
        is_adset_budget_sharing_enabled: "false",
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_create_adset",
  "Create an ad set. Requires page_id and/or pixel_id per campaign type.",
  {
    campaign_id: z.string(),
    name: z.string(),
    daily_budget: z.number().int().positive().describe("Daily budget in account currency cents"),
    optimization_goal: z.string(),
    billing_event: z.string().optional().default("IMPRESSIONS"),
    page_id: z.string().optional(),
    pixel_id: z.string().optional(),
    custom_event_type: z.string().optional(),
    lead_gen_form_id: z.string().optional(),
    targeting: z.record(z.unknown()).optional(),
    status: z.enum(["PAUSED", "ACTIVE"]).optional().default("PAUSED"),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    const promoted: Record<string, string> = {};
    if (args.page_id) promoted.page_id = args.page_id;
    if (args.pixel_id) promoted.pixel_id = args.pixel_id;
    if (args.custom_event_type) promoted.custom_event_type = args.custom_event_type;
    if (args.lead_gen_form_id) promoted.lead_gen_form_id = args.lead_gen_form_id;

    const targeting =
      args.targeting ||
      ({
        geo_locations: { countries: ["ES"] },
        age_min: 18,
      } as Record<string, unknown>);

    try {
      const data = await graph.post(graph.adAccountPath("adsets"), {
        campaign_id: args.campaign_id,
        name: args.name,
        daily_budget: args.daily_budget,
        optimization_goal: args.optimization_goal,
        billing_event: args.billing_event,
        bid_strategy: "LOWEST_COST_WITHOUT_CAP",
        status: args.status,
        promoted_object: JSON.stringify(promoted),
        targeting: JSON.stringify(targeting),
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_upload_ad_image",
  "Upload image bytes to ad account library; returns image hash.",
  {
    image_url: z.string().url().optional(),
    image_base64: z.string().optional(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      let bytes: Buffer;
      if (args.image_url) {
        const res = await fetch(args.image_url);
        if (!res.ok) throw new Error(`Failed to fetch image: ${res.status}`);
        bytes = Buffer.from(await res.arrayBuffer());
      } else if (args.image_base64) {
        bytes = Buffer.from(args.image_base64, "base64");
      } else {
        throw new Error("Provide image_url or image_base64");
      }
      const form = new FormData();
      form.append("bytes", new Blob([new Uint8Array(bytes)]), "creative.jpg");
      const data = await graph.postMultipart<{ images: Record<string, { hash: string }> }>(
        graph.adAccountPath("adimages"),
        form,
      );
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_create_ad_creative",
  "Create ad creative with page_id (required for most formats).",
  {
    name: z.string(),
    page_id: z.string(),
    message: z.string().optional(),
    link: z.string().url().optional(),
    image_hash: z.string().optional(),
    call_to_action_type: z.string().optional(),
    lead_gen_form_id: z.string().optional(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      let objectStorySpec: Record<string, unknown>;
      if (args.lead_gen_form_id) {
        objectStorySpec = {
          page_id: args.page_id,
          lead_gen_data: {
            call_to_action: {
              type: args.call_to_action_type || "SIGN_UP",
              value: { lead_gen_form_id: args.lead_gen_form_id },
            },
          },
        };
      } else {
        objectStorySpec = {
          page_id: args.page_id,
          link_data: {
            message: args.message || "",
            link: args.link || `https://facebook.com/${args.page_id}`,
            image_hash: args.image_hash,
            call_to_action: args.call_to_action_type
              ? { type: args.call_to_action_type, value: { link: args.link } }
              : undefined,
          },
        };
      }
      const data = await graph.post(graph.adAccountPath("adcreatives"), {
        name: args.name,
        object_story_spec: JSON.stringify(objectStorySpec),
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_create_ad",
  "Create ad linking ad set to creative.",
  {
    adset_id: z.string(),
    name: z.string(),
    creative_id: z.string(),
    status: z.enum(["PAUSED", "ACTIVE"]).optional().default("PAUSED"),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      const data = await graph.post(graph.adAccountPath("ads"), {
        name: args.name,
        adset_id: args.adset_id,
        creative: JSON.stringify({ creative_id: args.creative_id }),
        status: args.status,
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_create_leadgen_form",
  "Create a basic instant lead form on a page.",
  {
    page_id: z.string(),
    name: z.string(),
    privacy_policy_url: z.string().url(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      const questions = JSON.stringify([
        { type: "FULL_NAME" },
        { type: "EMAIL" },
        { type: "PHONE" },
      ]);
      const data = await graph.post(`${args.page_id}/leadgen_forms`, {
        name: args.name,
        privacy_policy_url: args.privacy_policy_url,
        questions,
        follow_up_action_url: args.privacy_policy_url,
      });
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_update_campaign",
  "Update campaign name, status, or budget fields.",
  {
    campaign_id: z.string(),
    name: z.string().optional(),
    status: z.enum(["PAUSED", "ACTIVE"]).optional(),
    daily_budget: z.number().int().positive().optional(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      const body: Record<string, string | number> = {};
      if (args.name) body.name = args.name;
      if (args.status) body.status = args.status;
      if (args.daily_budget) body.daily_budget = args.daily_budget;
      const data = await graph.post(args.campaign_id, body);
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_update_adset",
  "Update ad set budget or status (budget changes clamped by META_BUDGET_CHANGE_MAX_PCT).",
  {
    adset_id: z.string(),
    name: z.string().optional(),
    status: z.enum(["PAUSED", "ACTIVE"]).optional(),
    daily_budget: z.number().int().positive().optional(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      let daily = args.daily_budget;
      if (daily !== undefined) {
        const current = await graph.get<{ daily_budget?: string }>(args.adset_id, {
          fields: "daily_budget",
        });
        const cur = Number(current.daily_budget || 0);
        if (cur > 0) {
          daily = clampBudgetChange(cur, daily, config.budgetChangeMaxPct);
        }
      }
      const body: Record<string, string | number> = {};
      if (args.name) body.name = args.name;
      if (args.status) body.status = args.status;
      if (daily !== undefined) body.daily_budget = daily;
      const data = await graph.post(args.adset_id, body);
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_update_ad",
  "Update ad status or name.",
  {
    ad_id: z.string(),
    name: z.string().optional(),
    status: z.enum(["PAUSED", "ACTIVE"]).optional(),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    try {
      const body: Record<string, string> = {};
      if (args.name) body.name = args.name;
      if (args.status) body.status = args.status;
      const data = await graph.post(args.ad_id, body);
      return jsonText(data);
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_suggest_optimizations",
  "Read-only recommendations from recent insights.",
  {
    level: z.enum(["campaign", "adset", "ad"]).default("campaign"),
    date_preset: z.enum(["last_7d", "last_14d", "last_30d"]).default("last_7d"),
    max_cpa: z.number().positive().optional(),
    min_roas: z.number().positive().optional(),
    min_spend: z.number().optional().default(10),
  },
  async (args) => {
    try {
      const raw = await graph.getWithRetry<{ data: InsightRow[] }>(
        graph.adAccountPath("insights"),
        {
          level: args.level,
          date_preset: args.date_preset,
          fields:
            "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,spend,impressions,actions",
          limit: "50",
        },
      );
      const suggestions = suggestFromInsights(raw.data || [], {
        level: args.level,
        maxCpa: args.max_cpa,
        minRoas: args.min_roas,
        minSpend: args.min_spend,
        budgetChangeMaxPct: config.budgetChangeMaxPct,
      });
      return jsonText({ suggestions, count: suggestions.length });
    } catch (e) {
      return errText(e);
    }
  },
);

server.tool(
  "meta_ads_apply_optimization_plan",
  "Apply pause/activate/budget actions from a plan JSON. Requires confirmed=true.",
  {
    plan: z.array(
      z.object({
        type: z.enum(["pause", "activate", "budget_increase", "budget_decrease"]),
        entity_type: z.enum(["campaign", "adset", "ad"]),
        entity_id: z.string(),
        proposed_budget_cents: z.number().int().positive().optional(),
      }),
    ),
    confirmed: z.boolean(),
  },
  async (args) => {
    if (!args.confirmed) {
      return errText(new Error("Set confirmed=true after user explicitly approves"));
    }
    const results: Array<{ entity_id: string; ok: boolean; detail: unknown }> = [];
    for (const step of args.plan) {
      try {
        const status =
          step.type === "pause"
            ? "PAUSED"
            : step.type === "activate"
              ? "ACTIVE"
              : undefined;
        if (step.entity_type === "campaign") {
          const body: Record<string, string | number> = {};
          if (status) body.status = status;
          if (step.proposed_budget_cents) body.daily_budget = step.proposed_budget_cents;
          results.push({
            entity_id: step.entity_id,
            ok: true,
            detail: await graph.post(step.entity_id, body),
          });
        } else if (step.entity_type === "adset") {
          const body: Record<string, string | number> = {};
          if (status) body.status = status;
          if (step.proposed_budget_cents) {
            const current = await graph.get<{ daily_budget?: string }>(step.entity_id, {
              fields: "daily_budget",
            });
            const cur = Number(current.daily_budget || 0);
            body.daily_budget = clampBudgetChange(
              cur,
              step.proposed_budget_cents,
              config.budgetChangeMaxPct,
            );
          }
          results.push({
            entity_id: step.entity_id,
            ok: true,
            detail: await graph.post(step.entity_id, body),
          });
        } else {
          const body: Record<string, string> = {};
          if (status) body.status = status;
          results.push({
            entity_id: step.entity_id,
            ok: true,
            detail: await graph.post(step.entity_id, body),
          });
        }
      } catch (e) {
        results.push({
          entity_id: step.entity_id,
          ok: false,
          detail: formatGraphError(e),
        });
      }
    }
    return jsonText({ results });
  },
);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
