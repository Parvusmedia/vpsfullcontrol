function requireEnv(name: string): string {
  const v = process.env[name]?.trim();
  if (!v) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return v;
}

export function loadConfig() {
  return {
    accessToken: requireEnv("META_ACCESS_TOKEN"),
    adAccountId: normalizeAdAccountId(
      process.env.META_AD_ACCOUNT_ID?.trim() || "act_149543758710373",
    ),
    appId: process.env.META_APP_ID?.trim() || "",
    apiVersion: process.env.META_API_VERSION?.trim() || "v21.0",
    budgetChangeMaxPct: Math.min(
      100,
      Math.max(1, Number(process.env.META_BUDGET_CHANGE_MAX_PCT || "20")),
    ),
  };
}

export type AppConfig = ReturnType<typeof loadConfig>;

export function normalizeAdAccountId(id: string): string {
  const t = id.trim();
  if (t.startsWith("act_")) return t;
  return `act_${t.replace(/^act_/, "")}`;
}
