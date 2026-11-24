const d = $input.first().json;
const c = $("Configuracion").first().json;
const now = Date.now();
if (now - d.started_ms > 60000) throw new Error("Execution expired before command");

const summary = d.summary || {};
if (summary.reason !== "auto_off_timer") {
  const p = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Madrid",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(now));
  const m = Number(p.find((x) => x.type === "hour").value) * 60 + Number(p.find((x) => x.type === "minute").value);
  const day = new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Madrid", weekday: "short" }).format(new Date());
  const weekend = day === "Sat" || day === "Sun";
  const start = weekend ? 18 * 60 : 18 * 60 + 30;
  const endExclusive = weekend ? 10 * 60 : 7 * 60 + 30;
  const inWindow = m >= start || m < endExclusive;
  if (!inWindow) throw new Error("Outside heating window before command");
}

if (c.dry_run || (!["production", "trigger"].includes($execution.mode) && !c.manual_commands))
  throw new Error("Commands disabled");
return [{ json: d }];