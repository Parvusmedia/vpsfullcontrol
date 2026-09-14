(function () {
  "use strict";

  var yearEl = document.getElementById("y");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach(function (el) {
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  var needLinks = Array.prototype.slice.call(document.querySelectorAll(".need-link"));
  function oaiEventId() {
    try {
      if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    } catch (e) {}
    return "ev_" + Date.now() + "_" + Math.random().toString(16).slice(2);
  }

  function oaiCookie(name) {
    var match = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&") + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : "";
  }

  function sendOpenAiCapi(type) {
    var key = "oaiq_" + type + "_" + location.pathname + location.hash;
    try {
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, "1");
    } catch (e) {}
    var eventId = oaiEventId();
    var dataType = type === "appointment_scheduled" ? "customer_action" : "contents";
    var params = new URLSearchParams(location.search);
    var oppref = params.get("oppref") || oaiCookie("__oppref") || "";
    if (typeof oaiq === "function") {
      oaiq("measure", type, { type: dataType }, { event_id: eventId });
    }
    fetch("/oai-event.php", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        id: eventId,
        type: type,
        source_url: location.href.split("#")[0] + (location.hash || ""),
        oppref: oppref,
        obref: oaiCookie("__obref") || "",
      }),
      keepalive: true,
    }).catch(function () {});
  }

  function syncOpenAiHashEvents() {
    var hash = (location.hash || "").replace(/^#/, "");
    if (hash === "chatgpt-ads") sendOpenAiCapi("contents_viewed");
    else if (hash === "contact") sendOpenAiCapi("appointment_scheduled");
  }

  function fireOpenAiLanding() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    var hash = (location.hash || "").replace(/^#/, "");
    if (hash === "chatgpt-ads") {
      sendOpenAiCapi("contents_viewed");
      return;
    }
    if (hash === "contact") {
      sendOpenAiCapi("appointment_scheduled");
      return;
    }
    if (path === "/chatgpt-ads") sendOpenAiCapi("contents_viewed");
    else if (path === "/") sendOpenAiCapi("contents_viewed");
  }

  fireOpenAiLanding();
  window.addEventListener("hashchange", syncOpenAiHashEvents);

  var sections = ["chatgpt-ads", "dco", "leads", "automation", "whatsapp", "insights"]
    .map(function (id) {
      return document.getElementById(id);
    })
    .filter(Boolean);

  function setActiveNeed(id) {
    needLinks.forEach(function (link) {
      link.classList.toggle("is-active", link.getAttribute("data-need") === id);
    });
  }

  if ("IntersectionObserver" in window && sections.length) {
    var sectionIo = new IntersectionObserver(
      function (entries) {
        var visible = entries
          .filter(function (e) {
            return e.isIntersecting;
          })
          .sort(function (a, b) {
            return b.intersectionRatio - a.intersectionRatio;
          })[0];
        if (visible && visible.target.id) setActiveNeed(visible.target.id);
      },
      { threshold: [0.35, 0.55], rootMargin: "-15% 0px -35% 0px" }
    );
    sections.forEach(function (sec) {
      sectionIo.observe(sec);
    });
  }

  function setupSwap(rootId, slideAttr, tabAttr, onChange) {
    var root = document.getElementById(rootId);
    if (!root) return;
    var slides = Array.prototype.slice.call(root.querySelectorAll(".slide[" + slideAttr + "]"));
    var tabs = Array.prototype.slice.call(root.querySelectorAll("[" + tabAttr + "]"));
    if (!slides.length) return;
    var idx = 0;
    var timer;

    function show(i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach(function (slide, n) {
        slide.classList.toggle("is-visible", n === idx);
      });
      tabs.forEach(function (tab, n) {
        var active = n === idx;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-pressed", active ? "true" : "false");
      });
      if (typeof onChange === "function") onChange(idx, tabs[idx] || null);
    }

    function start() {
      if (timer) window.clearInterval(timer);
      timer = window.setInterval(function () {
        show(idx + 1);
      }, 5200);
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        show(parseInt(tab.getAttribute(tabAttr), 10));
        start();
      });
    });

    root.addEventListener("mouseenter", function () {
      if (timer) window.clearInterval(timer);
    });
    root.addEventListener("mouseleave", start);
    show(0);
    start();
  }

  var dcoSection = document.getElementById("dco");
  function applyDcoTheme(theme) {
    if (!dcoSection) return;
    var themes = ["weather", "performance", "signals"];
    themes.forEach(function (t) {
      dcoSection.classList.toggle("is-" + t, t === theme);
    });
    dcoSection.setAttribute("data-dco-theme", theme);

    var caseEl = dcoSection.querySelector(".dco-case");
    var titleEl = dcoSection.querySelector(".dco-title");
    var dekEl = dcoSection.querySelector(".dco-dek");
    if (caseEl) caseEl.textContent = caseEl.getAttribute("data-case-" + theme) || caseEl.textContent;
    if (titleEl) titleEl.textContent = titleEl.getAttribute("data-title-" + theme) || titleEl.textContent;
    if (dekEl) dekEl.textContent = dekEl.getAttribute("data-dek-" + theme) || dekEl.textContent;

    dcoSection.querySelectorAll(".dco-list li").forEach(function (li) {
      var forTheme = li.getAttribute("data-for");
      if (!forTheme) return;
      li.hidden = forTheme !== theme;
    });
  }

  setupSwap("dco", "data-dco", "data-dco-tab", function (_idx, tab) {
    var theme = (tab && tab.getAttribute("data-theme")) || "weather";
    applyDcoTheme(theme);
  });

  var waSection = document.getElementById("whatsapp");
  function applyWaTheme(theme) {
    if (!waSection) return;
    var themes = ["recovery", "upsell"];
    themes.forEach(function (t) {
      waSection.classList.toggle("is-" + t, t === theme);
    });
    waSection.setAttribute("data-wa-theme", theme);
  }
  setupSwap("wa-swap", "data-wa", "data-wa-tab", function (_idx, tab) {
    var theme = (tab && tab.getAttribute("data-theme")) || "recovery";
    applyWaTheme(theme);
  });
  applyWaTheme("recovery");

  var aiSection = document.getElementById("insights");
  function applyAiTheme(theme) {
    if (!aiSection) return;
    var themes = ["reports", "social"];
    themes.forEach(function (t) {
      aiSection.classList.toggle("is-" + t, t === theme);
    });
    aiSection.setAttribute("data-ai-theme", theme);

    var caseEl = aiSection.querySelector(".ai-case");
    var titleEl = aiSection.querySelector(".ai-title");
    var dekEl = aiSection.querySelector(".ai-dek");
    if (caseEl) caseEl.textContent = caseEl.getAttribute("data-case-" + theme) || caseEl.textContent;
    if (titleEl) titleEl.textContent = titleEl.getAttribute("data-title-" + theme) || titleEl.textContent;
    if (dekEl) dekEl.textContent = dekEl.getAttribute("data-dek-" + theme) || dekEl.textContent;

    aiSection.querySelectorAll(".ai-list li").forEach(function (li) {
      var forTheme = li.getAttribute("data-for");
      if (!forTheme) return;
      li.hidden = forTheme !== theme;
    });
  }

  setupSwap("ai-swap", "data-ai", "data-ai-tab", function (_idx, tab) {
    var theme = (tab && tab.getAttribute("data-theme")) || "reports";
    applyAiTheme(theme);
  });
  applyAiTheme("reports");

  document.querySelectorAll("[data-interest]").forEach(function (el) {
    el.addEventListener("click", function () {
      var field = document.getElementById("contact-interest");
      if (field) field.value = el.getAttribute("data-interest") || "";
    });
  });

  var form = document.getElementById("contact-form");
  var statusEl = document.getElementById("form-status");
  var captchaQ = document.getElementById("captcha-question");
  var captchaToken = document.getElementById("captcha-token");
  var captchaInput = document.getElementById("captcha");
  var captchaRefresh = document.getElementById("captcha-refresh");
  var captchaEndpoint = "/contact.php?action=captcha";

  var PHONE_COUNTRIES = [
    ["+34", "Spain"],
    ["+971", "United Arab Emirates"],
    ["+1", "United States / Canada"],
    ["+44", "United Kingdom"],
    ["+93", "Afghanistan"],
    ["+355", "Albania"],
    ["+213", "Algeria"],
    ["+376", "Andorra"],
    ["+244", "Angola"],
    ["+54", "Argentina"],
    ["+374", "Armenia"],
    ["+61", "Australia"],
    ["+43", "Austria"],
    ["+994", "Azerbaijan"],
    ["+973", "Bahrain"],
    ["+880", "Bangladesh"],
    ["+32", "Belgium"],
    ["+591", "Bolivia"],
    ["+387", "Bosnia"],
    ["+55", "Brazil"],
    ["+359", "Bulgaria"],
    ["+56", "Chile"],
    ["+86", "China"],
    ["+57", "Colombia"],
    ["+506", "Costa Rica"],
    ["+385", "Croatia"],
    ["+357", "Cyprus"],
    ["+420", "Czechia"],
    ["+45", "Denmark"],
    ["+593", "Ecuador"],
    ["+20", "Egypt"],
    ["+503", "El Salvador"],
    ["+372", "Estonia"],
    ["+358", "Finland"],
    ["+33", "France"],
    ["+995", "Georgia"],
    ["+49", "Germany"],
    ["+30", "Greece"],
    ["+502", "Guatemala"],
    ["+504", "Honduras"],
    ["+852", "Hong Kong"],
    ["+36", "Hungary"],
    ["+354", "Iceland"],
    ["+91", "India"],
    ["+62", "Indonesia"],
    ["+353", "Ireland"],
    ["+972", "Israel"],
    ["+39", "Italy"],
    ["+81", "Japan"],
    ["+962", "Jordan"],
    ["+7", "Kazakhstan"],
    ["+254", "Kenya"],
    ["+965", "Kuwait"],
    ["+371", "Latvia"],
    ["+961", "Lebanon"],
    ["+370", "Lithuania"],
    ["+352", "Luxembourg"],
    ["+60", "Malaysia"],
    ["+356", "Malta"],
    ["+52", "Mexico"],
    ["+377", "Monaco"],
    ["+212", "Morocco"],
    ["+31", "Netherlands"],
    ["+64", "New Zealand"],
    ["+505", "Nicaragua"],
    ["+234", "Nigeria"],
    ["+389", "North Macedonia"],
    ["+47", "Norway"],
    ["+968", "Oman"],
    ["+92", "Pakistan"],
    ["+507", "Panama"],
    ["+595", "Paraguay"],
    ["+51", "Peru"],
    ["+63", "Philippines"],
    ["+48", "Poland"],
    ["+351", "Portugal"],
    ["+974", "Qatar"],
    ["+40", "Romania"],
    ["+7", "Russia"],
    ["+966", "Saudi Arabia"],
    ["+381", "Serbia"],
    ["+65", "Singapore"],
    ["+421", "Slovakia"],
    ["+386", "Slovenia"],
    ["+27", "South Africa"],
    ["+82", "South Korea"],
    ["+46", "Sweden"],
    ["+41", "Switzerland"],
    ["+886", "Taiwan"],
    ["+66", "Thailand"],
    ["+216", "Tunisia"],
    ["+90", "Turkey"],
    ["+380", "Ukraine"],
    ["+598", "Uruguay"],
    ["+58", "Venezuela"],
    ["+84", "Vietnam"],
  ];

  function guessPhoneCc() {
    var tz = "";
    try {
      tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    } catch (e) {}
    var map = {
      "Europe/Madrid": "+34",
      "Atlantic/Canary": "+34",
      "Africa/Ceuta": "+34",
      "Asia/Dubai": "+971",
      "Europe/London": "+44",
      "America/New_York": "+1",
      "America/Chicago": "+1",
      "America/Denver": "+1",
      "America/Los_Angeles": "+1",
      "America/Toronto": "+1",
      "America/Mexico_City": "+52",
      "America/Bogota": "+57",
      "America/Argentina/Buenos_Aires": "+54",
      "America/Santiago": "+56",
      "America/Sao_Paulo": "+55",
      "America/Lima": "+51",
      "Europe/Paris": "+33",
      "Europe/Berlin": "+49",
      "Europe/Rome": "+39",
      "Europe/Lisbon": "+351",
      "Asia/Riyadh": "+966",
      "Asia/Qatar": "+974",
      "Asia/Kuwait": "+965",
    };
    if (map[tz]) return map[tz];
    var lang = (navigator.language || "").toLowerCase();
    if (lang.indexOf("es-mx") === 0) return "+52";
    if (lang.indexOf("es-ar") === 0) return "+54";
    if (lang.indexOf("es-co") === 0) return "+57";
    if (lang.indexOf("es-cl") === 0) return "+56";
    if (lang.indexOf("pt-br") === 0) return "+55";
    if (lang.indexOf("en-gb") === 0) return "+44";
    if (lang.indexOf("en-us") === 0) return "+1";
    if (lang.indexOf("fr") === 0) return "+33";
    if (lang.indexOf("de") === 0) return "+49";
    if (lang.indexOf("ar") === 0) return "+971";
    if (lang.indexOf("es") === 0) return "+34";
    return "+34";
  }

  function fillPhoneCountrySelects() {
    var preferred = ["+34", "+971", "+1", "+44"];
    var seen = {};
    var options = [];
    function add(cc, name) {
      if (seen[cc + name]) return;
      seen[cc + name] = true;
      options.push([cc, name]);
    }
    preferred.forEach(function (cc) {
      PHONE_COUNTRIES.forEach(function (row) {
        if (row[0] === cc) add(row[0], row[1]);
      });
    });
    PHONE_COUNTRIES.slice()
      .sort(function (a, b) {
        return a[1].localeCompare(b[1]);
      })
      .forEach(function (row) {
        add(row[0], row[1]);
      });
    var guessed = guessPhoneCc();
    document.querySelectorAll("select.phone-cc").forEach(function (select) {
      var current = select.value || guessed;
      select.innerHTML = "";
      options.forEach(function (row) {
        var opt = document.createElement("option");
        opt.value = row[0];
        opt.textContent = row[1] + " (" + row[0] + ")";
        select.appendChild(opt);
      });
      select.value = current;
      if (!select.value) select.value = guessed;
    });
  }

  fillPhoneCountrySelects();

  function applyCaptcha(payload) {
    if (!payload) return;
    if (captchaQ) captchaQ.textContent = payload.question || "Security check";
    if (captchaToken) captchaToken.value = payload.token || "";
    if (captchaInput) captchaInput.value = "";
  }

  function loadCaptcha() {
    return fetch(captchaEndpoint, { headers: { Accept: "application/json" }, cache: "no-store" })
      .then(function (res) {
        return res.json();
      })
      .then(function (body) {
        if (body && body.ok) applyCaptcha(body);
        else throw new Error("captcha");
      })
      .catch(function () {
        if (captchaQ) captchaQ.textContent = "Could not load check — tap refresh";
      });
  }

  if (captchaRefresh) {
    captchaRefresh.addEventListener("click", function () {
      loadCaptcha();
    });
  }
  if (form && captchaToken) {
    loadCaptcha();
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (statusEl) {
        statusEl.classList.remove("error", "ok");
        statusEl.textContent = "Sending…";
      }
      var data = new FormData(form);
      if (data.get("website")) {
        if (statusEl) {
          statusEl.classList.add("ok");
          statusEl.textContent = "Thanks — we’ll be in touch.";
        }
        form.reset();
        fillPhoneCountrySelects();
        loadCaptcha();
        return;
      }
      fetch(form.action, {
        method: "POST",
        body: data,
        headers: { Accept: "application/json" },
      })
        .then(function (res) {
          return res.json().then(function (body) {
            return { ok: res.ok, body: body };
          });
        })
        .then(function (result) {
          if (result.ok && result.body && result.body.ok) {
            if (statusEl) {
              statusEl.classList.add("ok");
              statusEl.textContent = "Thanks — your message was sent to hello@parvusmedia.com.";
            }
            form.reset();
            fillPhoneCountrySelects();
            loadCaptcha();
            return;
          }
          if (result.body && result.body.captcha) {
            applyCaptcha(result.body.captcha);
          } else {
            loadCaptcha();
          }
          if (statusEl) {
            statusEl.classList.add("error");
            statusEl.textContent =
              result.body && result.body.error === "Captcha failed"
                ? "Security check failed — please try again."
                : "Could not send. Please check the form and try again.";
          }
        })
        .catch(function () {
          var subject = encodeURIComponent(
            "Parvus Media inquiry" + (form.company.value ? " — " + form.company.value : "")
          );
          var phoneCc = form.phone_cc ? form.phone_cc.value : "";
          var phone = form.phone ? form.phone.value : "";
          var body = encodeURIComponent(
            "Name: " +
              form.name.value +
              "\nEmail: " +
              form.email.value +
              "\nPhone: " +
              phoneCc +
              " " +
              phone +
              "\nCompany: " +
              form.company.value +
              "\n\n" +
              form.message.value
          );
          if (statusEl) statusEl.textContent = "Opening your email to hello@parvusmedia.com…";
          window.location.href = "mailto:hello@parvusmedia.com?subject=" + subject + "&body=" + body;
        });
    });
  }
})();
