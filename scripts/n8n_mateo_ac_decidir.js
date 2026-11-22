// Decidir temperatura — Mateo (AC infrared_ac; un solo comando Tuya por petición)
const c = $("Configuracion").first().json;
const get = (n) => $(n).first().json;
const now = Date.now();
const store = $getWorkflowStaticData("global");
const autoOffMs = (c.auto_off_minutes || 30) * 60 * 1000;
const summary = {
  checked_at: new Date(now).toISOString(),
  room: c.room || "Mateo",
  sensor_id: c.sensor_id,
  ac_device_id: c.radiator_id,
  ir_hub_id: c.ir_hub_id,
  dry_run: c.dry_run,
  execution_mode: $execution.mode,
  status: "blocked",
  commands: [],
};

function madridDay(dayOverride) {
  return (
    dayOverride ||
    new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Madrid", weekday: "short" }).format(new Date())
  );
}

function inWindow(m, dayOverride) {
  const weekend = madridDay(dayOverride) === "Sat" || madridDay(dayOverride) === "Sun";
  const start = weekend ? 18 * 60 : 18 * 60 + 30;
  const endExclusive = weekend ? 10 * 60 : 7 * 60 + 30;
  return m >= start || m < endExclusive;
}

function autoOffAction(t, minC, offAboveC) {
  if (t >= offAboveC) return "off";
  return "extend";
}

const modeKey = { "0": "cold", "1": "heat", "2": "auto", "3": "wind_dry", "4": "dehumidification" };
const modeVal = { cold: "0", heat: "1", auto: "2", wind_dry: "3", dehumidification: "4" };
const fanKey = { "0": "auto", "1": "low", "2": "mid", "3": "high" };
const fanVal = { auto: "0", low: "1", mid: "2", high: "3" };

function acNorm(s) {
  const m = s?.mode;
  const f = s?.fan;
  return {
    switch_on: s?.switch_power === true,
    temperature: s?.temperature,
    mode: typeof m === "string" && m.length === 1 ? modeKey[m] || m : m,
    fan: typeof f === "string" && f.length === 1 ? fanKey[f] || f : f,
  };
}

/** Tuya infrared_ac: exactamente un comando por POST (varios → error 1109). */
function planOne(t, raw, m, dayOverride) {
  const s = acNorm(raw);
  if (!inWindow(m, dayOverride) || t >= c.min_c) return [];
  const ready =
    s.switch_on && s.temperature === c.target_c && s.mode === c.target_mode && s.fan === c.target_fan;
  if (ready) return [];
  if (!s.switch_on || s.temperature !== c.target_c) return [{ code: "temp", value: c.target_c }];
  if (s.mode !== c.target_mode) return [{ code: "mode", value: modeVal[c.target_mode] }];
  if (s.fan !== c.target_fan) return [{ code: "wind", value: fanVal[c.target_fan] }];
  return [{ code: "power", value: 1 }];
}

function isHeatOnCommand(cmd) {
  return cmd.code === "temp" || (cmd.code === "power" && cmd.value === 1);
}

function buildSend(summary, commands, should_send, extra) {
  const out = {
    summary,
    should_send,
    access_token: $("Tuya Token").first().json.result.access_token,
    tuya_method: "POST",
    tuya_path: "/v1.0/devices/" + c.radiator_id + "/commands",
    tuya_body: JSON.stringify({ commands }),
    started_ms: now,
    ...extra,
  };
  if (should_send && commands.length && isHeatOnCommand(commands[0])) {
    store.mateo_ac_auto_off_at = now + autoOffMs;
    summary.auto_off_at = new Date(store.mateo_ac_auto_off_at).toISOString();
    summary.auto_off_minutes = c.auto_off_minutes || 30;
  }
  if (!commands.length || (commands[0].code === "power" && commands[0].value === 0)) {
    store.mateo_ac_auto_off_at = null;
  }
  return [{ json: out }];
}

const off = { switch_power: false, temperature: 20, mode: "1", fan: "0" };
const onOk = { switch_power: true, temperature: c.target_c, mode: modeVal[c.target_mode], fan: fanVal[c.target_fan] };
if (planOne(c.min_c - 0.1, off, 1110, "Mon").length !== 1) throw new Error("Weekday 18:30 self-test failed");
if (planOne(c.min_c - 0.1, off, 1110, "Mon")[0].code !== "temp") throw new Error("AC start must be temp command");
if (planOne(c.min_c, off, 1110, "Mon").length !== 0) throw new Error("At threshold expect no command");
if (planOne(c.min_c + 0.1, off, 1110, "Mon").length !== 0) throw new Error("Above threshold expect no command");
if (planOne(c.min_c - 0.1, onOk, 1200, "Mon").length !== 0) throw new Error("Already configured expect no command");
if (planOne(c.min_c - 0.1, off, 449, "Mon").length !== 1) throw new Error("Weekday 07:29 self-test failed");
if (planOne(c.min_c - 0.1, off, 450, "Mon").length !== 0) throw new Error("After 07:30 weekday expect no heat");
if (planOne(c.min_c - 0.1, off, 1109, "Mon").length !== 0) throw new Error("Before 18:30 weekday expect no heat");
if (planOne(c.min_c - 0.1, off, 1080, "Sat").length !== 1) throw new Error("Weekend 18:00 self-test failed");
if (planOne(c.min_c - 0.1, off, 600, "Sun").length !== 0) throw new Error("Weekend 10:00 expect no heat");
const offAbove = c.auto_off_above_c ?? 22;
if (autoOffAction(22, c.min_c, offAbove) !== "off") throw new Error("Auto-off at 22C must off");
if (autoOffAction(21.5, c.min_c, offAbove) !== "extend") throw new Error("Auto-off below 22 extend");
if (autoOffAction(20.5, c.min_c, offAbove) !== "extend") throw new Error("Auto-off below 21 extend");

summary.logic_tests = 13;

if (c.force_ac_test) {
  if (["production", "trigger"].includes($execution.mode)) throw new Error("force_ac_test solo en ejecución manual");
  summary.commands = [{ code: "temp", value: c.target_c }];
  summary.status = "force_test";
  summary.reason = "force_ac_test";
  return buildSend(summary, summary.commands, !c.dry_run, {});
}

const parts = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Madrid",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
}).formatToParts(new Date(now));
const localMinutes = Number(parts.find((p) => p.type === "hour").value) * 60 + Number(parts.find((p) => p.type === "minute").value);
summary.timezone = "Europe/Madrid";
summary.window = "18:30-07:30 (lun-vie), 18:00-10:00 (sab-dom)";
summary.in_window = inWindow(localMinutes);
summary.threshold_c = c.min_c;
summary.auto_off_above_c = offAbove;
const offAtPending = store.mateo_ac_auto_off_at;
summary.auto_off_scheduled_at = offAtPending ? new Date(offAtPending).toISOString() : null;
const autoOffDue = Boolean(offAtPending && now >= offAtPending);

const apiNames = ["Conexion sensor", "Temperatura sensor", "Conexion radiador", "Estado radiador"];
for (const n of apiNames) {
  const r = get(n);
  if (r.success !== true) {
    summary.reason = "api_error";
    summary.failed_step = n;
    summary.api_code = String(r.code || "network_error");
    return [{ json: { summary, should_send: false } }];
  }
}
if (get("Conexion sensor").result?.online !== true || get("Conexion radiador").result?.online !== true) {
  summary.reason = "device_offline";
  return [{ json: { summary, should_send: false } }];
}

const props = get("Temperatura sensor").result?.properties || [];
const p = props.find((x) => x.code === c.temperature_code);
const unit = props.find((x) => x.code === "temp_unit_convert");
if (!p || typeof p.value !== "number" || !Number.isFinite(p.value) || unit?.value !== "c") {
  summary.reason = "invalid_temperature_or_unit";
  return [{ json: { summary, should_send: false } }];
}

const t = p.value / Math.pow(10, c.scale);
let ts = Number(p.time);
if (ts < 1e12) ts *= 1000;
summary.temperature_c = t;
summary.reading_at = Number.isFinite(ts) ? new Date(ts).toISOString() : null;
summary.age_minutes = (now - ts) / 60000;

if (t < -20 || t > 60 || !Number.isFinite(ts) || ts <= 0 || ts > now + 60000) {
  summary.reason = "invalid_temperature_or_timestamp";
  return [{ json: { summary, should_send: false } }];
}

const rp = get("Estado radiador").result?.properties || [];
const rawState = Object.fromEntries(rp.map((x) => [x.code, x.value]));
summary.ac = { ...rawState, normalized: acNorm(rawState) };
if (typeof rawState.switch_power !== "boolean" || typeof rawState.temperature !== "number") {
  summary.reason = "invalid_ac_state";
  return [{ json: { summary, should_send: false } }];
}

const ac = acNorm(rawState);
const manual = !["production", "trigger"].includes($execution.mode);
const permitted = !c.dry_run && (!manual || c.manual_commands);

if (autoOffDue) {
  summary.auto_off_due = true;
  if (ac.switch_on) {
    const action = autoOffAction(t, c.min_c, offAbove);
    summary.auto_off_action = action;
    if (action === "off") {
      summary.commands = [{ code: "power", value: 0 }];
      summary.status = "auto_off";
      summary.reason = "auto_off_timer";
      return buildSend(summary, summary.commands, permitted, { reading_ms: ts });
    }
    const nextAt = now + autoOffMs;
    store.mateo_ac_auto_off_at = nextAt;
    summary.status = "no_change";
    summary.reason = t < c.min_c ? "auto_off_extended_below_min" : "auto_off_extended_below_off_above";
    summary.auto_off_extended_to = new Date(nextAt).toISOString();
    summary.temperature_c = t;
    return [{ json: { summary, should_send: false, reading_ms: ts, started_ms: now } }];
  }
  store.mateo_ac_auto_off_at = null;
  summary.status = "no_change";
  summary.reason = "auto_off_timer_already_off";
  return [{ json: { summary, should_send: false, reading_ms: ts, started_ms: now } }];
}

if (ac.switch_on && !offAtPending) {
  summary.reason = "already_on_no_timer";
}

summary.commands = planOne(t, rawState, localMinutes);
summary.status = summary.commands.length ? "commands_required" : "no_change";
summary.reason = !summary.in_window
  ? "outside_window"
  : summary.commands.length
    ? "ac_adjust"
    : ac.switch_on
      ? "already_on"
      : t < c.min_c
        ? "below_" + c.min_c
        : "temperature_not_below_threshold";

if (summary.commands.length && !permitted) summary.status = "dry_run";

const should_send = permitted && summary.commands.length > 0;
return buildSend(summary, summary.commands, should_send, { reading_ms: ts });