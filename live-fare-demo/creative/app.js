(function () {
  "use strict";

  const CONFIG = {
    feedUrl: "https://flights.pmediaplus.com/fares/network.json",
    defaultOrigin: "JED",
    maxDataAgeMinutes: 30,
    fetchTimeoutMs: 4000,
    fallbackOrigin: "JED",
    fallbackOriginName: "Jeddah",
    fallbackDestination: "RUH",
    fallbackDestinationName: "Riyadh",
    fallbackDeeplink: "https://www.saudia.com/booking?B_LOCATION=JED&E_LOCATION=RUH&trip_type=OW&DATE_1=2026-10-15T00:00:00",
    bookingBase: "https://www.saudia.com/booking",
    clickTag: ""
  };

  const MONTHS = [
    { value: "2026-10", label: "October 2026" },
    { value: "2026-11", label: "November 2026" },
    { value: "2026-12", label: "December 2026" }
  ];

  const COUNTRY_ORDER = ["SA", "AE", "US"];
  const COUNTRY_LABEL = {
    SA: "Saudi Arabia",
    AE: "United Arab Emirates",
    US: "United States"
  };

  const params = new URLSearchParams(window.location.search);
  const debugEnabled = params.get("debug") === "1";

  function resolveFeedUrl() {
    if (debugEnabled && params.get("feed")) return params.get("feed");
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "flights.pmediaplus.com") {
      return "/fares/network.json";
    }
    return CONFIG.feedUrl;
  }

  const els = {
    origin: document.getElementById("origin"),
    destination: document.getElementById("destination"),
    month: document.getElementById("month"),
    priceKicker: document.getElementById("priceKicker"),
    priceValue: document.getElementById("priceValue"),
    routeLine: document.getElementById("routeLine"),
    cta: document.getElementById("cta"),
    debug: document.getElementById("debug"),
    banner: document.getElementById("banner"),
    hint: document.getElementById("interactHint"),
    cueOrigin: document.getElementById("cueOrigin"),
    cueDest: document.getElementById("cueDest")
  };

  let feed = null;
  let feedLoaded = false;
  let feedError = "";
  let currentFare = null;
  let cueTimers = [];
  let cueDone = false;

  function originMeta() {
    const list = (feed && feed.origins) || [];
    const map = {};
    list.forEach(function (item) {
      map[item.code] = item;
    });
    return map;
  }

  function selectedOriginMeta() {
    const code = els.origin.value || CONFIG.fallbackOrigin;
    return originMeta()[code] || {
      code: code,
      name: code,
      country: "",
      country_name: ""
    };
  }

  function cityLabel(name, code) {
    if (!code) return name || "";
    if (!name || name === code) return code;
    if (name.indexOf("(" + code + ")") !== -1) return name;
    return name + " (" + code + ")";
  }

  function destinationsForOrigin(origin) {
    const seen = {};
    const out = [];
    if (!feed || !Array.isArray(feed.fares)) return out;
    feed.fares.forEach(function (fare) {
      if (fare.origin !== origin || seen[fare.destination]) return;
      seen[fare.destination] = true;
      out.push({
        code: fare.destination,
        name: fare.destination_name || fare.destination
      });
    });
    out.sort(function (a, b) { return a.name.localeCompare(b.name); });
    return out;
  }

  function fillOriginSelect() {
    const previous = els.origin.value;
    els.origin.innerHTML = "";
    const origins = ((feed && feed.origins) || []).slice();
    origins.sort(function (a, b) {
      const ca = COUNTRY_ORDER.indexOf(a.country);
      const cb = COUNTRY_ORDER.indexOf(b.country);
      if (ca !== cb) return (ca === -1 ? 99 : ca) - (cb === -1 ? 99 : cb);
      return String(a.name).localeCompare(String(b.name));
    });
    const groups = {};
    origins.forEach(function (item) {
      const key = item.country || "XX";
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });
    COUNTRY_ORDER.concat(Object.keys(groups)).forEach(function (country) {
      if (groups[country] && !els.origin.querySelector('optgroup[data-country="' + country + '"]')) {
        const group = document.createElement("optgroup");
        group.label = COUNTRY_LABEL[country] || groups[country][0].country_name || country;
        group.setAttribute("data-country", country);
        groups[country].forEach(function (item) {
          const opt = document.createElement("option");
          opt.value = item.code;
          opt.textContent = cityLabel(item.name, item.code);
          group.appendChild(opt);
        });
        els.origin.appendChild(group);
        delete groups[country];
      }
    });
    const preferred = previous || CONFIG.defaultOrigin;
    if ([].some.call(els.origin.options, function (opt) { return opt.value === preferred; })) {
      els.origin.value = preferred;
    } else if (els.origin.options.length) {
      els.origin.selectedIndex = 0;
    }
  }

  function fillDestinationSelect() {
    const previous = els.destination.value;
    const dests = destinationsForOrigin(els.origin.value);
    els.destination.innerHTML = "";
    dests.forEach(function (item) {
      const opt = document.createElement("option");
      opt.value = item.code;
      opt.textContent = cityLabel(item.name, item.code);
      els.destination.appendChild(opt);
    });
    if ([].some.call(els.destination.options, function (opt) { return opt.value === previous; })) {
      els.destination.value = previous;
    } else if ([].some.call(els.destination.options, function (opt) { return opt.value === CONFIG.fallbackDestination; })) {
      els.destination.value = CONFIG.fallbackDestination;
    } else if (els.destination.options.length) {
      els.destination.selectedIndex = 0;
    }
  }

  function fillSelect(select, items, getValue, getLabel) {
    select.innerHTML = "";
    items.forEach(function (item) {
      const opt = document.createElement("option");
      opt.value = getValue(item);
      opt.textContent = getLabel(item);
      select.appendChild(opt);
    });
  }

  function fillCueMenu(menu, select, count) {
    if (!menu || !select) return;
    menu.innerHTML = "";
    const seen = {};
    [].forEach.call(select.options, function (opt) {
      if (!opt.value || seen[opt.value] || menu.childNodes.length >= count) return;
      seen[opt.value] = true;
      const row = document.createElement("div");
      row.textContent = opt.textContent;
      menu.appendChild(row);
    });
  }

  function fieldOf(select) {
    return select ? select.closest(".field") : null;
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function clearCue() {
    cueTimers.forEach(function (id) { window.clearTimeout(id); });
    cueTimers = [];
    [].forEach.call(els.banner.querySelectorAll(".field"), function (field) {
      field.classList.remove("is-cue", "is-open-cue");
    });
  }

  function scheduleCue(fn, ms) {
    cueTimers.push(window.setTimeout(fn, ms));
  }

  function pulseHint() {
    if (!els.hint) return;
    els.hint.classList.remove("is-pulse");
    void els.hint.offsetWidth;
    els.hint.classList.add("is-pulse");
  }

  function stopInteractCue() {
    if (cueDone) {
      clearCue();
      return;
    }
    cueDone = true;
    clearCue();
    pulseHint();
  }

  function playInteractCue() {
    if (cueDone) return;
    fillCueMenu(els.cueOrigin, els.origin, 3);
    fillCueMenu(els.cueDest, els.destination, 3);
    const originField = fieldOf(els.origin);
    const destField = fieldOf(els.destination);
    const monthField = fieldOf(els.month);

    if (
      prefersReducedMotion() ||
      !originField ||
      !destField ||
      !els.cueOrigin.childNodes.length
    ) {
      cueDone = true;
      pulseHint();
      return;
    }

    scheduleCue(function () {
      originField.classList.add("is-cue", "is-open-cue");
    }, 500);
    scheduleCue(function () {
      originField.classList.remove("is-open-cue");
    }, 2100);
    scheduleCue(function () {
      originField.classList.remove("is-cue");
      fillCueMenu(els.cueDest, els.destination, 3);
      destField.classList.add("is-cue", "is-open-cue");
    }, 2400);
    scheduleCue(function () {
      destField.classList.remove("is-open-cue");
    }, 4100);
    scheduleCue(function () {
      destField.classList.remove("is-cue");
      if (monthField) monthField.classList.add("is-cue");
    }, 4400);
    scheduleCue(function () {
      if (monthField) monthField.classList.remove("is-cue");
      cueDone = true;
      pulseHint();
    }, 5400);
  }

  function getClickTag() {
    if (typeof window.clickTag === "string" && window.clickTag) return window.clickTag;
    if (typeof window.clickTAG === "string" && window.clickTAG) return window.clickTAG;
    return params.get("clickTag") || CONFIG.clickTag || "";
  }

  function saudiaBookingUrl(origin, destination, month) {
    const from = origin || CONFIG.fallbackOrigin;
    const to = destination || CONFIG.fallbackDestination;
    const when = month || "2026-10";
    return CONFIG.bookingBase
      + "?B_LOCATION=" + encodeURIComponent(from)
      + "&E_LOCATION=" + encodeURIComponent(to)
      + "&trip_type=OW"
      + "&DATE_1=" + encodeURIComponent(when + "-15T00:00:00");
  }

  function resolveExitUrl(deeplink) {
    const dest = deeplink || saudiaBookingUrl(
      els.origin && els.origin.value,
      els.destination && els.destination.value,
      els.month && els.month.value
    );
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

  function findFare(origin, dest, month) {
    if (!feed || !Array.isArray(feed.fares)) return null;
    for (let i = 0; i < feed.fares.length; i += 1) {
      const fare = feed.fares[i];
      if (fare.origin === origin && fare.destination === dest && fare.month === month) {
        return fare;
      }
    }
    return null;
  }

  function formatPrice(amount, currency) {
    if (typeof amount !== "number" || Number.isNaN(amount)) return null;
    const symbols = { EUR: "€", USD: "$", GBP: "£" };
    if (symbols[currency]) return symbols[currency] + Math.round(amount);
    return (currency || "SAR") + " " + Math.round(amount);
  }

  function currentBookingUrl() {
    return saudiaBookingUrl(els.origin.value, els.destination.value, els.month.value);
  }

  function showFallback(reason) {
    const origin = selectedOriginMeta();
    const destName = (els.destination.options[els.destination.selectedIndex] || {}).textContent || CONFIG.fallbackDestinationName;
    currentFare = null;
    els.banner.classList.add("is-fallback");
    els.priceKicker.textContent = "Fly " + (origin.name || CONFIG.fallbackOriginName) + " → " + destName;
    els.priceValue.textContent = "Discover our latest fares";
    els.priceValue.classList.add("fallback");
    els.routeLine.textContent = "";
    els.cta.setAttribute("href", resolveExitUrl(currentBookingUrl()));
    renderDebug(reason);
  }

  function showFare(fare) {
    const formatted = formatPrice(fare.price, fare.currency || "SAR");
    if (!formatted) {
      showFallback("invalid-price");
      return;
    }
    currentFare = fare;
    els.banner.classList.remove("is-fallback");
    els.priceKicker.textContent = "From";
    els.priceValue.textContent = formatted;
    els.priceValue.classList.remove("fallback");
    els.routeLine.textContent =
      (fare.origin_name || fare.origin) + " → " + (fare.destination_name || fare.destination);
    els.cta.setAttribute("href", resolveExitUrl(currentBookingUrl()));
    renderDebug("ok");
  }

  function updateView() {
    if (!feedLoaded || !feed || !isFresh(feed.updated_at)) {
      showFallback(!feedLoaded ? (feedError || "feed-unavailable") : "stale");
      return;
    }
    const fare = findFare(els.origin.value, els.destination.value, els.month.value);
    if (!fare) {
      showFallback("missing-combo");
      return;
    }
    showFare(fare);
  }

  function onOriginChange() {
    stopInteractCue();
    fillDestinationSelect();
    updateView();
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
    const fareKey = [els.origin.value, els.destination.value, els.month.value].join("-");
    const lines = [
      "Feed loaded: " + (feedLoaded && feed ? "YES" : "NO"),
      "Updated: " + (feed && feed.updated_at ? clock(feed.updated_at) : "n/a"),
      "Age: " + (feed && feed.updated_at ? ageLabel(feed.updated_at) : "n/a"),
      "Feed URL: " + resolveFeedUrl(),
      "Fare: " + fareKey,
      "Book: " + currentBookingUrl(),
      "Price: " + (currentFare ? currentFare.price + " " + (currentFare.currency || "") : "fallback"),
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
      fillOriginSelect();
      fillDestinationSelect();
    }).catch(function (err) {
      feed = null;
      feedLoaded = false;
      feedError = err && err.name === "AbortError" ? "timeout" : "feed-unavailable";
    }).then(function () {
      window.clearTimeout(timer);
      updateView();
      playInteractCue();
    });
  }

  fillSelect(els.month, MONTHS, function (m) { return m.value; }, function (m) {
    return m.label;
  });
  els.month.value = "2026-10";
  els.origin.addEventListener("change", onOriginChange);
  els.destination.addEventListener("change", function () {
    stopInteractCue();
    updateView();
  });
  els.month.addEventListener("change", function () {
    stopInteractCue();
    updateView();
  });
  [els.origin, els.destination, els.month].forEach(function (select) {
    select.addEventListener("pointerdown", stopInteractCue);
  });
  els.cta.addEventListener("click", function (event) {
    const url = resolveExitUrl(currentBookingUrl());
    els.cta.setAttribute("href", url);
    if (!url) event.preventDefault();
  });

  showFallback("loading");
  fetchFeed();
})();
