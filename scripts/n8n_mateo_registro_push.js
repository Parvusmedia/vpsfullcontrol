const prev = $input.first().json;
const s = $("Preparar push SmartLife").first().json.summary || {};
const push_ok = prev.success === true && prev.result?.send_status === true;
return [
  {
    json: {
      summary: {
        ...s,
        push_sent: push_ok,
        push_send_status: prev.result?.send_status ?? null,
        push_api_code: prev.success === false ? String(prev.code ?? "") : "",
        push_api_msg: prev.success === false ? String(prev.msg ?? "") : "",
      },
    },
  },
];