import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { GET } from "../api/dashboard";

async function main(): Promise<void> {
  const outDir = join(process.cwd(), "public");
  const outPath = join(outDir, "dashboard.json");

  const res = await GET(new Request("http://snapshot.local/dashboard"));
  const body = await res.text();

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(body) as Record<string, unknown>;
  } catch {
    console.error("[snapshot] handler did not return JSON");
    process.exit(1);
  }

  parsed._delivery = "build_snapshot";
  parsed.snapshot_built_at = new Date().toISOString();

  mkdirSync(outDir, { recursive: true });
  writeFileSync(outPath, JSON.stringify(parsed), "utf8");

  console.log(
    `[snapshot] ${outPath} source=${String(parsed.source)} rows=${
      Array.isArray(parsed.cumplimiento) ? parsed.cumplimiento.length : 0
    }`
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
