(function (root) {
  "use strict";

  var host = window.location.hostname;
  var local = host === "localhost" || host === "127.0.0.1";
  var API = local ? "http://127.0.0.1:8021" : "";

  function api(path, opts) {
    return fetch(API + path, Object.assign({
      headers: { "Content-Type": "application/json" }
    }, opts || {})).then(function (res) {
      if (!res.ok) throw new Error("network");
      return res.json();
    });
  }

  var events = JSON.parse(sessionStorage.getItem("usj_events") || "[]");

  function track(name, payload) {
    var row = { name: name, payload: payload || {}, t: Date.now() };
    events.push(row);
    sessionStorage.setItem("usj_events", JSON.stringify(events.slice(-80)));
    if (window.console && console.info) console.info("[advisor]", name, payload || {});
    api("/api/events", { method: "POST", body: JSON.stringify({ name: name, payload: payload || {} }) }).catch(function () {});
  }

  function debugEnabled() {
    return new URLSearchParams(location.search).get("debug") === "1";
  }

  function saveState(state) {
    sessionStorage.setItem("usj_state", JSON.stringify(state));
  }

  function loadState() {
    try { return JSON.parse(sessionStorage.getItem("usj_state") || "{}"); }
    catch (e) { return {}; }
  }

  function clickThrough(url) {
    if (!url) return;
    if (window.clickTag) {
      window.open(String(window.clickTag) + encodeURIComponent(url), "_blank");
      return;
    }
    window.open(url, "_blank");
  }

  root.USJ = {
    api: api,
    track: track,
    events: function () { return events.slice(); },
    debugEnabled: debugEnabled,
    saveState: saveState,
    loadState: loadState,
    clickThrough: clickThrough
  };
})(window);
