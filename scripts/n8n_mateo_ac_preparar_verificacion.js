const r = $input.first().json;
const c = $("Configuracion").first().json;

if (r.success !== true) {
  throw new Error(
    "Tuya command rejected: code=" + String(r.code ?? "?") + " msg=" + String(r.msg ?? "unknown")
  );
}

const resultOk = r.result === true || r.result === "true";
if (!resultOk && !c.force_ac_test) {
  throw new Error(
    "Tuya command rejected: result=" +
      JSON.stringify(r.result) +
      " (code=" +
      String(r.code ?? "") +
      " msg=" +
      String(r.msg ?? "") +
      ")"
  );
}

return [
  {
    json: {
      access_token: $("Tuya Token").first().json.result.access_token,
      tuya_path: "/v2.0/cloud/thing/" + c.radiator_id + "/shadow/properties",
      command_ack: { success: r.success, result: r.result, code: r.code, msg: r.msg },
    },
  },
];