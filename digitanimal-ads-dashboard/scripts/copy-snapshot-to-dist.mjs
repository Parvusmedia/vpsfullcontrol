#!/usr/bin/env node
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "public", "dashboard.json");
if (!existsSync(src)) {
  console.error("[copy-snapshot] missing public/dashboard.json");
  process.exit(1);
}

const targets = [join(root, "dist", "dashboard.json"), join(root, "dist", "static", "dashboard.json")];
for (const dest of targets) {
  mkdirSync(dirname(dest), { recursive: true });
  copyFileSync(src, dest);
  console.log(`[copy-snapshot] -> ${dest}`);
}
