import http from "node:http";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const sample = JSON.parse(
  readFileSync(join(__dirname, "../src/data/sample-payload.json"), "utf8")
);

const port = Number(process.env.API_PORT ?? 5181);

const server = http.createServer(async (req, res) => {
  if (req.url !== "/api/dashboard" && req.url !== "/dashboard") {
    res.writeHead(404);
    res.end();
    return;
  }
  const url = process.env.DIGITANIMAL_SHEETS_JSON_URL;
  res.setHeader("Content-Type", "application/json");
  if (!url) {
    res.end(
      JSON.stringify({
        source: "sample",
        message:
          "Muestra local. En producción: Apps Script + DIGITANIMAL_SHEETS_JSON_URL.",
        ...sample,
      })
    );
    return;
  }
  try {
    const r = await fetch(url);
    const body = await r.text();
    res.statusCode = r.ok ? 200 : 502;
    res.end(body);
  } catch (e) {
    res.statusCode = 502;
    res.end(JSON.stringify({ source: "error", message: String(e), ...sample }));
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`dev-api on http://127.0.0.1:${port}`);
});
