/**
 * OpenAI Ads measurement pixel — init + top-up (order_created).
 * Pixel ID is public; Conversions API key stays server-side only.
 */
(function () {
  const PIXEL_ID = "NQH4BHyBvLncEkDLpUrQpJ";
  const SDK = "https://bzrcdn.openai.com/sdk/oaiq.min.js";
  const TOPUP_SOURCE = "https://companydataenrichment.com/salesnav/panel/#topup";

  const debug =
    /(?:^|[?&])oaiq_debug=1(?:&|$)/.test(window.location.search) ||
    window.localStorage.getItem("oaiq_debug") === "1";

  if (!window.oaiq) {
    (function (w, d, s, u) {
      if (w.oaiq) return;
      const q = function () {
        q.q.push(arguments);
      };
      q.q = [];
      w.oaiq = q;
      const j = d.createElement(s);
      j.async = 1;
      j.src = u;
      const f = d.getElementsByTagName(s)[0];
      f.parentNode.insertBefore(j, f);
    })(window, document, "script", SDK);
  }

  window.oaiq("init", { pixelId: PIXEL_ID, debug: debug });

  /**
   * @param {{ eventId: string, amountCents?: number, currency?: string, packId?: string }} opts
   */
  window.cdeOpenAiAdsMeasureTopup = function (opts) {
    const eventId = (opts && opts.eventId ? String(opts.eventId) : "").trim();
    if (!eventId || typeof window.oaiq !== "function") return false;

    const dedupeKey = "sn_oaiq_topup_" + eventId;
    try {
      if (sessionStorage.getItem(dedupeKey)) return false;
      sessionStorage.setItem(dedupeKey, "1");
    } catch {
      /* continue */
    }

    const amount = Math.max(0, Number(opts.amountCents) || 0);
    const currency = (opts.currency || "EUR").toUpperCase();
    const data = { type: "contents", amount: amount, currency: currency };
    const packId = opts.packId ? String(opts.packId) : "";
    if (packId) {
      data.contents = [
        {
          id: packId,
          name: "Sales Navigator credits",
          content_type: "product",
          quantity: 1,
        },
      ];
    }

    window.oaiq("measure", "order_created", data, { event_id: eventId });
    return true;
  };

  window.cdeOpenAiAdsTopupSourceUrl = TOPUP_SOURCE;
})();
