import { readFileSync } from "node:fs";
import { loadConfig } from "./config.js";
import { formatGraphError, GraphClient } from "./graph.js";

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
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {
    /* optional */
  }
}

loadDotEnv();

async function run(): Promise<void> {
  const config = loadConfig();
  const graph = new GraphClient(config);
  const report: Record<string, unknown> = { ad_account_id: config.adAccountId };

  try {
    report.account = await graph.get(config.adAccountId, {
      fields: "id,name,account_status,currency,timezone_name,funding_source_details",
    });
  } catch (e) {
    report.account_error = formatGraphError(e);
  }

  try {
    report.campaigns = await graph.get(graph.adAccountPath("campaigns"), {
      fields: "id,name,status,effective_status",
      limit: "5",
    });
  } catch (e) {
    report.campaigns_error = formatGraphError(e);
  }

  try {
    report.pages = await graph.get(graph.adAccountPath("promote_pages"), {
      fields: "id,name",
      limit: "10",
    });
  } catch (e) {
    report.pages_error = formatGraphError(e);
  }

  try {
    report.pixels = await graph.get(graph.adAccountPath("adspixels"), {
      fields: "id,name",
      limit: "10",
    });
  } catch (e) {
    report.pixels_error = formatGraphError(e);
  }

  try {
    report.insights = await graph.get(graph.adAccountPath("insights"), {
      level: "campaign",
      date_preset: "last_7d",
      fields: "campaign_name,spend,impressions",
      limit: "5",
    });
  } catch (e) {
    report.insights_error = formatGraphError(e);
  }

  console.log(JSON.stringify(redactSecrets(report), null, 2));
}

function redactSecrets(value: unknown): unknown {
  if (typeof value === "string") {
    return value.replace(/access_token=[^&\s"]+/gi, "access_token=REDACTED");
  }
  if (Array.isArray(value)) return value.map(redactSecrets);
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) {
      out[k] = redactSecrets(v);
    }
    return out;
  }
  return value;
}

run().catch((e) => {
  console.error(formatGraphError(e));
  process.exit(1);
});
