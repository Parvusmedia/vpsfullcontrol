let s = {};
try {
  s = $("Preparar push SmartLife").first().json.summary || {};
} catch {
  s = $input.first().json.summary || {};
}
const prev = $input.first().json;
const push_ok = prev?.success === true && prev?.result?.send_status === true;
const push_err = prev?.error?.message || (prev?.success === false ? String(prev?.msg || prev?.message || "") : "");
return [
  {
    json: {
      summary: {
        ...s,
        push_sent: push_ok,
        push_skipped: s.push_skipped === true,
        push_send_status: prev?.result?.send_status ?? null,
        push_api_code: prev?.success === false ? String(prev?.code ?? "") : "",
        push_api_msg: push_ok ? "" : push_err || String(prev?.msg || ""),
      },
    },
  },
];