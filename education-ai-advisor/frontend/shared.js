(function (root) {
  "use strict";

  var host = window.location.hostname;
  var local = host === "localhost" || host === "127.0.0.1";
  var API = local ? "http://127.0.0.1:8022" : "";

  function api(path, opts) {
    return fetch(API + path, Object.assign({
      headers: { "Content-Type": "application/json" }
    }, opts || {})).then(function (res) {
      if (!res.ok) throw new Error("network");
      return res.json();
    });
  }

  var events = JSON.parse(sessionStorage.getItem("edu_events") || "[]");

  function track(name, payload) {
    var row = { name: name, payload: payload || {}, t: Date.now() };
    events.push(row);
    sessionStorage.setItem("edu_events", JSON.stringify(events.slice(-80)));
    if (window.console && console.info) console.info("[advisor]", name, payload || {});
    api("/api/events", { method: "POST", body: JSON.stringify({ name: name, payload: payload || {} }) }).catch(function () {});
  }

  function debugEnabled() {
    return new URLSearchParams(location.search).get("debug") === "1";
  }

  function presentEnabled() {
    return new URLSearchParams(location.search).get("present") === "1";
  }

  function scenarioParam() {
    return new URLSearchParams(location.search).get("scenario");
  }

  function appendPresent(href) {
    if (!presentEnabled()) return href;
    try {
      var u = new URL(href, location.origin);
      u.searchParams.set("present", "1");
      return u.pathname + u.search;
    } catch (e) {
      return href;
    }
  }

  function appendScenario(href, scenario) {
    if (!scenario) return href;
    try {
      var u = new URL(href, location.origin);
      u.searchParams.set("scenario", scenario);
      return u.pathname + u.search;
    } catch (e) {
      return href;
    }
  }

  function saveState(state) {
    sessionStorage.setItem("edu_state", JSON.stringify(state));
  }

  function loadState() {
    try { return JSON.parse(sessionStorage.getItem("edu_state") || "{}"); }
    catch (e) { return {}; }
  }

  function clickThrough(url) {
    if (!url) return;
    if (window.clickTag) {
      window.open(String(window.clickTag) + encodeURIComponent(url), "_blank");
      return;
    }
    var opened = window.open(url, "_blank");
    if (!opened && window.top) window.top.location.href = url;
  }

  function whatsappText(ctx) {
    ctx = ctx || {};
    var prefix = "Hi, I would like information about";
    var programme = ctx.programme || "";
    var labels = ctx.labels || [];
    var text = prefix;
    if (programme) text += " " + programme;
    else text += " graduate programmes at Demo University";
    if (labels.length) text += ". My profile: " + labels.join(", ");
    return text + ".";
  }

  function whatsappUrl(ctx) {
    return "https://api.whatsapp.com/send/?phone=" + encodeURIComponent("+447700900123") +
      "&text=" + encodeURIComponent(whatsappText(ctx)) +
      "&app_absent=0";
  }

  function openWhatsApp(ctx) {
    track("whatsapp_clicked", {
      programme: ctx && ctx.programme,
      labels: ctx && ctx.labels
    });
    clickThrough(whatsappUrl(ctx));
  }

  function submitLead(data) {
    return api("/api/lead", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  function prefetch(href, as) {
    var head = document.head;
    if (!head || head.querySelector('link[rel="prefetch"][href="' + href + '"]')) return;
    var el = document.createElement("link");
    el.rel = "prefetch";
    el.href = href;
    if (as) el.as = as;
    head.appendChild(el);
  }

  root.EDU = {
    api: api,
    track: track,
    events: function () { return events.slice(); },
    debugEnabled: debugEnabled,
    presentEnabled: presentEnabled,
    scenarioParam: scenarioParam,
    appendPresent: appendPresent,
    appendScenario: appendScenario,
    saveState: saveState,
    loadState: loadState,
    clickThrough: clickThrough,
    whatsappText: whatsappText,
    whatsappUrl: whatsappUrl,
    openWhatsApp: openWhatsApp,
    submitLead: submitLead,
    prefetch: prefetch
  };
})(window);
