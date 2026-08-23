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

  function resolveStepActive(active) {
    if (active === "orientador") return "anuncio";
    if (active === "concepto" || active === "anuncio" || active === "destino") return active;
    return null;
  }

  function hrefWithFlags(href) {
    href = USJ.appendPresent ? USJ.appendPresent(href) : href;
    return href;
  }

  function renderDemoMap(active) {
    var stepActive = resolveStepActive(active);
    var activeIdx = -1;
    if (stepActive) {
      for (var i = 0; i < STEPS.length; i++) {
        if (STEPS[i].id === stepActive) {
          activeIdx = i;
          break;
        }
      }
    }
    return STEPS.map(function (step, i) {
      var cls = "demo-pill";
      var hintExtra = "";
      if (stepActive && step.id === stepActive) {
        cls += " active";
        hintExtra = "Estás aquí · ";
      } else if (activeIdx >= 0 && i === activeIdx + 1) {
        cls += " demo-pill-next";
        hintExtra = "Siguiente · ";
      } else if (activeIdx >= 0 && i < activeIdx) {
        cls += " demo-pill-done";
      }
      return (
        '<a class="' + cls + '" href="' + hrefWithFlags(step.href) + '">' +
        '<span class="num" aria-hidden="true">' + step.num + "</span>" +
        "<div><b>" + step.title + "</b><small>" + hintExtra + step.hint + "</small></div></a>"
      );
    }).join("");
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

  function renderDemoRef() {
    var nav = document.querySelector(".nav");
    if (!nav || document.querySelector(".demo-ref")) return;
    nav.insertAdjacentHTML(
      "afterend",
      '<div class="demo-ref" aria-label="Referencia del producto">' +
      "<span>Universidad San Jorge</span>" +
      "<strong>Orientador en display</strong>" +
      "</div>"
    );
  }

  function positionMapMount() {
    var mount = document.getElementById("demo-map-mount");
    if (!mount) {
      var ref = document.querySelector(".demo-ref");
      var nav = document.querySelector(".nav");
      var anchor = ref || nav;
      if (!anchor) return null;
      anchor.insertAdjacentHTML(
        "afterend",
        '<div id="demo-map-mount" class="demo-map-mount demo-map-mount-top"></div>'
      );
      return document.getElementById("demo-map-mount");
    }
    mount.classList.add("demo-map-mount-top");
    mount.hidden = false;
    var refNode = document.querySelector(".demo-ref");
    if (refNode && mount.previousElementSibling !== refNode) {
      refNode.insertAdjacentElement("afterend", mount);
    }
    return mount;
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
    var active = opts.active || detectActive();
    enhanceNav();
    renderDemoRef();
    var mapMount = positionMapMount();
    if (mapMount) {
      mapMount.innerHTML =
        '<div class="demo-map-rail" aria-label="Recorrido del demo">' +
        '<p class="demo-map-label">Recorrido del demo</p>' +
        '<div class="demo-map">' + renderDemoMap(active) + "</div></div>";
    }

    var hereMount = document.getElementById("demo-here-mount");
    if (hereMount) hereMount.innerHTML = "";

    var linearMount = document.getElementById("demo-linear-mount");
    if (linearMount) {
      linearMount.innerHTML = "";
      linearMount.hidden = true;
    }

    prefetchForStep(active);
  };
})(window);
