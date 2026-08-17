(function () {
  "use strict";

  const CONFIG = {
    feedUrl: "https://flights.pmediaplus.com/fares/MAD.json",
    origin: "MAD",
    originName: "Madrid",
    maxDataAgeMinutes: 30,
    fetchTimeoutMs: 3000,
    fallbackDestination: "RUH",
    fallbackDestinationName: "Riyadh",
    fallbackDeeplink: "https://example.com/book?origin=MAD&destination=RUH",
    clickTag: ""
  };

  const DESTINATIONS = [
    { code: "RUH", name: "Riyadh" },
    { code: "JED", name: "Jeddah" },
    { code: "DXB", name: "Dubai" }
  ];

  const MONTHS = [
    { value: "2026-10", label: "October 2026" },
    { value: "2026-11", label: "November 2026" },
    { value: "2026-12", label: "December 2026" }
  ];

  const params = new URLSearchParams(window.location.search);
  const debugEnabled = params.get("debug") === "1";

  function resolveFeedUrl() {
    if (debugEnabled && params.get("feed")) return params.get("feed");
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") return "/fares/MAD.json";
    return CONFIG.feedUrl;
  }

  const els = {
    destination: document.getElementById("destination"),
    month: document.getElementById("month"),
    originLabel: document.getElementById("originLabel"),
    priceKicker: document.getElementById("priceKicker"),
    priceValue: document.getElementById("priceValue"),
    routeLine: document.getElementById("routeLine"),
    priceBlock: document.getElementById("priceBlock"),
    cta: document.getElementById("cta"),
    debug: document.getElementById("debug"),
    banner: document.getElementById("banner")
  };

  let feed = null;
  let feedLoaded = false;
  let feedError = "";
  let currentFare = null;

  function fillSelect(select, items, getValue, getLabel) {
    select.innerHTML = "";
    items.forEach(function (item) {
      const opt = document.createElement("option");
      opt.value = getValue(item);
      opt.textContent = getLabel(item);
      select.appendChild(opt);
    });
  }

  function selectedDestination() {
    return DESTINATIONS.find(function (d) {
      return d.code === els.destination.value;
    }) || DESTINATIONS[0];
  }

  function getClickTag() {
    if (typeof window.clickTag === "string" && window.clickTag) return window.clickTag;
    if (typeof window.clickTAG === "string" && window.clickTAG) return window.clickTAG;
    return params.get("clickTag") || CONFIG.clickTag || "";
  }

  function resolveExitUrl(deeplink) {
    const dest = deeplink || CONFIG.fallbackDeeplink;
    const tag = getClickTag();
    if (!tag) return dest;
    if (/[?&](?:url|dest|adurl)=?$/i.test(tag) || /[=]$/.test(tag)) {
      return tag + encodeURIComponent(dest);
    }
    return tag;
  }

  function isFresh(updatedAt) {
    const parsed = Date.parse(updatedAt);
    if (Number.isNaN(parsed)) return false;
    return Date.now() - parsed <= CONFIG.maxDataAgeMinutes * 60 * 1000;
  }

  function findFare(dest, month) {
    if (!feed || !Array.isArray(feed.fares)) return null;
    for (let i = 0; i < feed.fares.length; i += 1) {
      const fare = feed.fares[i];
      if (fare.destination === dest && fare.month === month) return fare;
    }
    return null;
  }

  function formatPrice(amount, currency) {
    if (typeof amount !== "number" || Number.isNaN(amount)) return null;
    const symbol = currency === "EUR" ? "€" : currency + " ";
    return "From " + symbol + Math.round(amount);
  }

  function showFallback(reason) {
    const dest = selectedDestination();
    currentFare = null;
    els.banner.classList.add("is-fallback");
    els.priceKicker.textContent = "Fly " + CONFIG.originName + " → " + dest.name;
    els.priceValue.textContent = "Discover our latest fares";
    els.priceValue.classList.add("fallback");
    els.routeLine.textContent = "";
    els.cta.setAttribute("href", resolveExitUrl(CONFIG.fallbackDeeplink));
    renderDebug(reason);
  }

  function showFare(fare) {
    const formatted = formatPrice(fare.price, fare.currency || "EUR");
    if (!formatted) {
      showFallback("invalid-price");
      return;
    }
    currentFare = fare;
    els.banner.classList.remove("is-fallback");
    els.priceKicker.textContent = "From";
    els.priceValue.textContent = formatted.replace(/^From /, "From ");
    els.priceValue.classList.remove("fallback");
    // Display as "FROM €379"
    els.priceValue.textContent = formatted.replace("From ", "FROM ");
    els.routeLine.textContent =
      CONFIG.originName + " → " + (fare.destination_name || fare.destination);
    els.cta.setAttribute("href", resolveExitUrl(fare.deeplink));
    renderDebug("ok");
  }

  function updateView() {
    const dest = els.destination.value;
    const month = els.month.value;
    if (!feedLoaded || !feed || !isFresh(feed.updated_at)) {
      showFallback(!feedLoaded ? (feedError || "feed-unavailable") : "stale");
      return;
    }
    const fare = findFare(dest, month);
    if (!fare) {
      showFallback("missing-combo");
      return;
    }
    showFare(fare);
  }

  function ageLabel(updatedAt) {
    const parsed = Date.parse(updatedAt);
    if (Number.isNaN(parsed)) return "n/a";
    const seconds = Math.max(0, Math.round((Date.now() - parsed) / 1000));
    if (seconds < 60) return seconds + " sec";
    return Math.round(seconds / 60) + " min";
  }

  function clock(updatedAt) {
    const parsed = Date.parse(updatedAt);
    if (Number.isNaN(parsed)) return "n/a";
    return new Date(parsed).toISOString().slice(11, 19);
  }

  function renderDebug(status) {
    if (!debugEnabled) return;
    const dest = selectedDestination();
    const fareKey = CONFIG.origin + "-" + dest.code + "-" + els.month.value;
    const lines = [
      "Feed loaded: " + (feedLoaded && feed ? "YES" : "NO"),
      "Updated: " + (feed && feed.updated_at ? clock(feed.updated_at) : "n/a"),
      "Age: " + (feed && feed.updated_at ? ageLabel(feed.updated_at) : "n/a"),
      "Feed URL: " + resolveFeedUrl(),
      "Fare: " + fareKey,
      "Price: " + (currentFare ? currentFare.price + " " + (currentFare.currency || "EUR") : "fallback"),
      "Status: " + status
    ];
    els.debug.hidden = false;
    els.debug.textContent = lines.join("\n");
  }

  function fetchFeed() {
    const controller = new AbortController();
    const timer = window.setTimeout(function () {
      controller.abort();
    }, CONFIG.fetchTimeoutMs);

    return fetch(resolveFeedUrl(), {
      method: "GET",
      credentials: "omit",
      cache: "no-cache",
      signal: controller.signal
    }).then(function (res) {
      if (!res.ok) throw new Error("http-" + res.status);
      return res.json();
    }).then(function (data) {
      if (!data || typeof data !== "object" || !Array.isArray(data.fares)) {
        throw new Error("invalid-json");
      }
      feed = data;
      feedLoaded = true;
      feedError = "";
    }).catch(function (err) {
      feed = null;
      feedLoaded = false;
      feedError = err && err.name === "AbortError" ? "timeout" : "feed-unavailable";
    }).then(function () {
      window.clearTimeout(timer);
      updateView();
    });
  }

  fillSelect(els.destination, DESTINATIONS, function (d) { return d.code; }, function (d) {
    return d.name;
  });
  fillSelect(els.month, MONTHS, function (m) { return m.value; }, function (m) {
    return m.label;
  });
  els.originLabel.textContent = CONFIG.originName + " (" + CONFIG.origin + ")";
  els.destination.value = CONFIG.fallbackDestination;
  els.month.value = "2026-10";

  els.destination.addEventListener("change", updateView);
  els.month.addEventListener("change", updateView);
  els.cta.addEventListener("click", function (event) {
    const url = resolveExitUrl(currentFare && currentFare.deeplink);
    els.cta.setAttribute("href", url);
    if (!url) {
      event.preventDefault();
    }
  });

  showFallback("loading");
  fetchFeed();
})();
