(function (root) {
  "use strict";

  var STEPS = [
    {
      id: "concepto",
      href: "/",
      num: "1",
      title: "Concepto",
      hint: "Orientador en el anuncio"
    },
    {
      id: "anuncio",
      href: "/ad/",
      num: "2",
      title: "Anuncio",
      hint: "Ejemplo interactivo"
    },
    {
      id: "destino",
      href: "/admissions",
      num: "3",
      title: "Destino USJ",
      hint: "CRM y WhatsApp"
    }
  ];

  var USJ = root.USJ || {};

  function detectActive() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    if (path === "/" || path === "/index.html") return "concepto";
    if (path === "/admin" || path.indexOf("/admin") === 0) return "catalogo";
    if (path === "/admissions" || path.indexOf("/admissions") === 0) return "destino";
    if (path === "/ad" || path.indexOf("/ad/") === 0) return "anuncio";
    if (path === "/orientador" || path.indexOf("/orientador") === 0) return "orientador";
    return "concepto";
  }

  function hrefWithFlags(href) {
    href = USJ.appendPresent ? USJ.appendPresent(href) : href;
    return href;
  }

  function renderDemoMap(active) {
    return STEPS.map(function (step) {
      var cls = "demo-pill";
      if (step.id === active) cls += " active";
      if (active === "concepto" && step.id === "anuncio") cls += " demo-pill-next";
      if (active === "anuncio" && step.id === "destino") cls += " demo-pill-next";
      return (
        '<a class="' + cls + '" href="' + hrefWithFlags(step.href) + '">' +
        '<span class="num">' + step.num + '</span>' +
        "<div><b>" + step.title + "</b><small>" + step.hint + "</small></div></a>"
      );
    }).join("");
  }

  function renderLinearNav(active) {
    var idx = -1;
    for (var i = 0; i < STEPS.length; i++) {
      if (STEPS[i].id === active) { idx = i; break; }
    }
    if (idx < 0) return "";
    var prev = idx > 0 ? STEPS[idx - 1] : null;
    var next = idx < STEPS.length - 1 ? STEPS[idx + 1] : null;
    var homeHref = hrefWithFlags("/");
    var prevHtml = prev
      ? '<a class="demo-nav-btn ghost" href="' + hrefWithFlags(prev.href) + '">← ' + prev.title + "</a>"
      : '<span class="demo-nav-spacer"></span>';
    var nextHtml = next
      ? '<a class="demo-nav-btn" href="' + hrefWithFlags(next.href) + '">' + next.title + " →</a>"
      : '<a class="demo-nav-btn ghost" href="' + homeHref + '">Volver al inicio</a>';
    return (
      '<nav class="demo-linear" aria-label="Recorrido">' +
      prevHtml +
      '<span class="demo-linear-count">Paso ' + STEPS[idx].num + " de 3</span>" +
      nextHtml +
      "</nav>"
    );
  }

  function enhanceNav() {
    var nav = document.querySelector(".nav");
    if (!nav || nav.dataset.enhanced === "1") return;
    nav.dataset.enhanced = "1";
    var brand = nav.querySelector(".brand");
    if (brand && !brand.querySelector(".nav-logo")) {
      brand.insertAdjacentHTML("afterbegin", '<img class="nav-logo" src="/logo.svg" alt="" width="36" height="36">');
      brand.classList.add("brand-with-logo");
    }
    if (!nav.querySelector(".nav-home")) {
      nav.insertAdjacentHTML("beforeend", '<a class="nav-home" href="' + hrefWithFlags("/") + '">Inicio</a>');
    }
  }

  function applyPresentMode() {
    if (USJ.presentEnabled && USJ.presentEnabled()) {
      document.body.classList.add("present-mode");
    }
  }

  function prefetchForStep(active) {
    if (!USJ.prefetch) return;
    if (active === "concepto") {
      USJ.prefetch("/ad/");
      USJ.prefetch("/ad/unit.html?size=300x600");
    } else if (active === "anuncio") {
      USJ.prefetch("/admissions");
    }
  }

  root.USJ = USJ;
  root.USJ.mountDemoChrome = function (opts) {
    opts = opts || {};
    applyPresentMode();
    enhanceNav();
    var active = opts.active || detectActive();
    var mapMount = document.getElementById("demo-map-mount");
    if (mapMount) {
      var mapClass = active === "concepto" ? "demo-map demo-map-compact" : "demo-map";
      mapMount.innerHTML = '<div class="' + mapClass + '">' + renderDemoMap(active) + "</div>";
    }

    var hereMount = document.getElementById("demo-here-mount");
    if (hereMount) hereMount.innerHTML = "";

    var linearMount = document.getElementById("demo-linear-mount");
    if (linearMount && active !== "catalogo" && active !== "orientador" && active !== "concepto") {
      linearMount.innerHTML = renderLinearNav(active);
    }

    prefetchForStep(active);
  };
})(window);
