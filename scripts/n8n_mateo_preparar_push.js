const c = $("Configuracion").first().json;
const s = $input.first().json.summary;
const templateId = String(c.push_template_id || "").trim();

function skip(reason) {
  return [{ json: { summary: { ...s, push_skipped: true, push_reason: reason } } }];
}

if (!c.notify_on_heat) return skip("notify_disabled");
if (!templateId) return skip("no_push_template_id");
if (!String(c.smartlife_uid || "").trim()) return skip("no_smartlife_uid");
const t = $("Tuya Token").first().json.result.access_token;
if (!t) throw new Error("Tuya authentication failed");

const params = {
  room: String(c.room || "Mateo"),
  temp: String(s.temperature_c ?? "?"),
  target: String(c.target_c ?? 21),
};
const body = {
  uid: c.smartlife_uid,
  biz_type: c.push_biz_type ?? 18,
  template_id: templateId,
};
if (c.push_template_use_params !== false) {
  body.template_param = JSON.stringify(params);
}

return [
  {
    json: {
      summary: s,
      access_token: t,
      tuya_path: "/v1.0/iot-03/messages/app-notifications/actions/push",
      tuya_body: JSON.stringify(body),
    },
  },
];