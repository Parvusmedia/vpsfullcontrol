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
  var sections = ["dco", "leads", "automation", "whatsapp", "insights"]
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

  var form = document.getElementById("contact-form");
  var statusEl = document.getElementById("form-status");
  var captchaQ = document.getElementById("captcha-question");
  var captchaToken = document.getElementById("captcha-token");
  var captchaInput = document.getElementById("captcha");
  var captchaRefresh = document.getElementById("captcha-refresh");
  var captchaEndpoint = "/contact.php?action=captcha";

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
          var body = encodeURIComponent(
            "Name: " +
              form.name.value +
              "\nEmail: " +
              form.email.value +
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
