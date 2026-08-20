(function (root) {
  "use strict";

  var STEPS = [
    {
      id: "orientador",
      href: "/orientador",
      num: "1",
      title: "Orientador",
      hint: "Empieza aquí · wizard web"
    },
    {
      id: "anuncio",
      href: "/ad",
      num: "2",
      title: "Anuncio",
      hint: "Creativos DSP-ready"
    },
    {
      id: "admisiones",
      href: "/admissions",
      num: "3",
      title: "Admisiones",
      hint: "Leads al CRM"
    }
  ];

  var USJ = root.USJ || {};

  function detectActive() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    if (path === "/" || path === "/index.html") return "hub";
    if (path === "/orientador" || path.indexOf("/orientador") === 0) return "orientador";
    if (path === "/admin" || path.indexOf("/admin") === 0) return "catalogo";
    if (path === "/admissions" || path.indexOf("/admissions") === 0) return "admisiones";
    if (path === "/ad" || path.indexOf("/ad/") === 0) return "anuncio";
    return "hub";
  }

  function hrefWithFlags(href) {
    href = USJ.appendPresent ? USJ.appendPresent(href) : href;
    return href;
  }

  function renderDemoMap(active) {
    return STEPS.map(function (step) {
      var cls = "demo-pill";
      if (step.id === active) cls += " active";
      if (active === "hub" && step.id === "orientador") cls += " demo-pill-next";
      return (
        '<a class="' + cls + '" href="' + hrefWithFlags(step.href) + '">' +
        '<span class="num">' + step.num + '</span>' +
        "<div><b>" + step.title + "</b><small>" + step.hint + "</small></div></a>"
      );
    }).join("");
  }

  function renderDemoGuide() {
    return (
      '<section class="demo-guide">' +
      '<p class="kicker">Recorrido</p>' +
      "<h2>Qué ver en cada paso</h2>" +
      '<ol class="demo-flow">' +
      "<li><span class=\"flow-num\">1</span><span><b>Orientador</b> — completa las 3 preguntas. Prueba abogado + derecho digital: recomienda IA Aplicada, no inventa un máster jurídico.</span></li>" +
      "<li><span class=\"flow-num\">2</span><span><b>Anuncio</b> — mismo motor en 300×600 y 970×250. Cierra por WhatsApp o formulario al CRM.</span></li>" +
      "<li><span class=\"flow-num\">3</span><span><b>Admisiones</b> — el lead aparece con perfil, % de encaje y alternativas. Vacío hasta que completes el paso 1 o 2.</span></li>" +
      "</ol></section>"
    );
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
      : '<a class="demo-nav-btn ghost" href="' + homeHref + '">Inicio</a>';
    var nextHtml = next
      ? '<a class="demo-nav-btn" href="' + hrefWithFlags(next.href) + '">' + next.title + " →</a>"
      : '<a class="demo-nav-btn ghost" href="' + homeHref + '">Fin del demo</a>";
    return (
      '<nav class="demo-linear" aria-label="Recorrido del demo">' +
      prevHtml +
      '<span class="demo-linear-count">Paso ' + STEPS[idx].num + " de 3</span>" +
      nextHtml +
      "</nav>"
    );
  }

  function hereBanner(active) {
    if (active === "hub") {
      return '<p class="demo-here">Estás en el <b>inicio del demo</b>. Los números del menú siguen el orden del recorrido: 1 Orientador → 2 Anuncio → 3 Admisiones.</p>';
    }
    if (active === "catalogo") {
      return '<p class="demo-here"><b>Catálogo</b> (referencia, fuera del recorrido). <a href="' + hrefWithFlags("/orientador") + '">Ir al paso 1 · Orientador</a> · <a href="' + hrefWithFlags("/") + '">Inicio del demo</a></p>';
    }
    var tips = {
      orientador: "Completa el wizard y pulsa <b>Seguir por WhatsApp</b> o <b>Dejar mis datos</b>. Siguiente: <a href=\"" + hrefWithFlags("/ad") + "\">Anuncio</a>.",
      anuncio: "Prueba los creativos embebidos. Siguiente: <a href=\"" + hrefWithFlags("/admissions") + "\">Admisiones</a> para ver el lead.",
      admisiones: "Si está vacío, vuelve al <a href=\"" + hrefWithFlags("/orientador") + "\">Orientador</a> y genera un lead."
    };
    return '<p class="demo-here">' + (tips[active] || "") + "</p>";
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
      nav.insertAdjacentHTML("beforeend", '<a class="nav-home" href="' + hrefWithFlags("/") + '">Inicio del demo</a>');
    }
  }

  function applyPresentMode() {
    if (USJ.presentEnabled && USJ.presentEnabled()) {
      document.body.classList.add("present-mode");
    }
  }

  function prefetchForStep(active) {
    if (!USJ.prefetch) return;
    if (active === "hub") {
      USJ.prefetch("/orientador");
      USJ.prefetch("/api/guide");
    } else if (active === "orientador") {
      USJ.prefetch("/ad/unit.html?size=300x600");
      USJ.prefetch("/ad");
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
      mapMount.innerHTML = '<div class="demo-map">' + renderDemoMap(active) + "</div>";
    }

    var hereMount = document.getElementById("demo-here-mount");
    if (hereMount) hereMount.innerHTML = hereBanner(active);

    var linearMount = document.getElementById("demo-linear-mount");
    if (linearMount && active !== "hub" && active !== "catalogo") {
      linearMount.innerHTML = renderLinearNav(active);
    }

    var guideMount = document.getElementById("demo-guide-mount");
    if (guideMount && opts.showGuide) guideMount.innerHTML = renderDemoGuide();

    prefetchForStep(active);
  };
})(window);
