/**
 * OpenAI Ads measurement pixel — landing (contents_viewed) + top-up (order_created).
 * Pixel ID is public; Conversions API key stays server-side only.
 */
(function () {
  const PIXEL_ID = "NQH4BHyBvLncEkDLpUrQpJ";
  const SDK = "https://bzrcdn.openai.com/sdk/oaiq.min.js";
  const LANDING_SOURCE = "https://companydataenrichment.com/salesnav/";
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

  function newLandingEventId() {
    return "landing_" + Date.now() + "_" + Math.random().toString(36).slice(2, 12);
  }

  function isSalesnavLanding() {
    if (!document.body || document.body.classList.contains("product-salesnav-panel")) {
      return false;
    }
    if (!document.body.classList.contains("product-salesnav")) {
      return false;
    }
    const path = window.location.pathname.replace(/\/+$/, "") || "/";
    return path === "/salesnav" || path === "/salesnav/index.html";
  }

  /**
   * Campaign arrival — https://companydataenrichment.com/salesnav/
   */
  function measureLandingContentsViewed() {
    if (!isSalesnavLanding() || typeof window.oaiq !== "function") return;

    const eventId = newLandingEventId();
    const data = { type: "contents" };
    window.oaiq("measure", "contents_viewed", data, { event_id: eventId });

    if (typeof fetch === "function") {
      fetch("/api/salesnav-ads-event.php", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "contents_viewed",
          event_id: eventId,
          source_url: LANDING_SOURCE,
        }),
      }).catch(function () {
        /* CAPI optional if OPENAI_CONVERSIONS_API_KEY unset */
      });
    }
  }

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

  window.cdeOpenAiAdsLandingSourceUrl = LANDING_SOURCE;
  window.cdeOpenAiAdsTopupSourceUrl = TOPUP_SOURCE;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", measureLandingContentsViewed);
  } else {
    measureLandingContentsViewed();
  }
})();
