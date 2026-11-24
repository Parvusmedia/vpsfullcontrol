const r = $input.first().json;
const s = $("Decidir temperatura").first().json.summary;
if (r.success !== true) throw new Error("Cannot verify AC state");
const st = Object.fromEntries((r.result?.properties || []).map((p) => [p.code, p.value]));
const modeVal = { cold: "0", heat: "1", auto: "2", wind_dry: "3", dehumidification: "4" };
const fanVal = { auto: "0", low: "1", mid: "2", high: "3" };

function isHeatOnCommand(cmd) {
  return cmd?.code === "temp" || (cmd?.code === "power" && cmd.value === 1);
}

function matches(cmd) {
  const v = cmd.value;
  if (cmd.code === "temp") return Number(st.temperature) === Number(v);
  if (cmd.code === "mode") return String(st.mode) === String(modeVal[v] ?? v);
  if (cmd.code === "wind") return String(st.fan) === String(fanVal[v] ?? v);
  if (cmd.code === "power") return String(st.switch_power ? 1 : 0) === String(v);
  return st[cmd.code] === v;
}

const mismatch = (s.commands || []).filter((x) => !matches(x)).map((x) => x.code);
const verified = mismatch.length === 0;
const heatOnSent = (s.commands || []).some(isHeatOnCommand);
const should_notify_heat =
  verified &&
  heatOnSent &&
  s.reason !== "auto_off_timer" &&
  s.reason !== "force_ac_test";

return [
  {
    json: {
      summary: {
        ...s,
        status: mismatch.length ? "verification_pending" : "verified",
        mismatch,
        should_notify_heat,
        verified_state: {
          switch_power: st.switch_power,
          temperature: st.temperature,
          mode: st.mode,
          fan: st.fan,
        },
      },
    },
  },
];