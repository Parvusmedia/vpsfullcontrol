(function (root) {
  "use strict";

  var STEPS = [
    {
      id: "catalogo",
      href: "/admin",
      num: "0",
      title: "Catálogo",
      hint: "Datos oficiales de los másteres"
    },
    {
      id: "anuncio",
      href: "/ad",
      num: "1",
      title: "Anuncio",
      hint: "HTML5 listos para DSP"
    },
    {
      id: "orientador",
      href: "/",
      num: "2",
      title: "Orientador",
      hint: "Experiencia web completa"
    },
    {
      id: "admisiones",
      href: "/admissions",
      num: "3",
      title: "Admisiones",
      hint: "Leads cualificados del equipo"
    }
  ];

  function detectActive() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    if (path === "/admin" || path.indexOf("/admin") === 0) return "catalogo";
    if (path === "/admissions" || path.indexOf("/admissions") === 0) return "admisiones";
    if (path === "/ad" || path.indexOf("/ad/") === 0) return "anuncio";
    return "orientador";
  }

  function renderDemoMap(active) {
    return STEPS.map(function (step) {
      var cls = "demo-pill" + (step.id === active ? " active" : "");
      return (
        '<a class="' + cls + '" href="' + step.href + '">' +
        '<span class="num">' + step.num + '</span>' +
        "<div><b>" + step.title + "</b><small>" + step.hint + "</small></div></a>"
      );
    }).join("");
  }

  function renderDemoGuide(active) {
    return (
      '<section class="demo-guide">' +
      '<p class="kicker">Recorrido del demo</p>' +
      "<h2>Qué ver y en qué orden</h2>" +
      '<p class="lede">Este enlace muestra el producto de punta a punta: datos estructurados, captación en display, orientación guiada y lo que recibe admisiones. No es la web pública de USJ: es un entorno de demostración con catálogo reducido (3 másteres).</p>' +
      '<ol class="demo-flow">' +
      "<li><span class=\"flow-num\">0</span><span><b>Catálogo</b> — de dónde salen plazas, modalidades y hechos que usa el motor (sin inventar con IA).</span></li>" +
      "<li><span class=\"flow-num\">1</span><span><b>Anuncio</b> — creativos DSP-ready en 300×600 y 970×250; cierre por WhatsApp o formulario al CRM de USJ.</span></li>" +
      "<li><span class=\"flow-num\">2</span><span><b>Orientador</b> — misma lógica en landing: prueba el caso abogado + derecho digital → IA Aplicada.</span></li>" +
      "<li><span class=\"flow-num\">3</span><span><b>Admisiones</b> — tras completar el flujo, el lead aparece aquí con perfil, encaje y alternativas.</span></li>" +
      "</ol></section>"
    );
  }

  function hereBanner(active) {
    var labels = {
      catalogo: "Estás en el <b>Catálogo</b> (paso 0). Siguiente: prueba el <a href=\"/ad\">Anuncio</a>.",
      anuncio: "Estás en el <b>Anuncio</b> (paso 1). Prueba un creativo DSP-ready y cierra por WhatsApp o formulario al CRM.",
      orientador: "Estás en el <b>Orientador</b> (paso 2). Empieza abajo o revisa antes el <a href=\"/admin\">Catálogo</a> y el <a href=\"/ad\">Anuncio</a>.",
      admisiones: "Estás en <b>Admisiones</b> (paso 3). Si no hay leads, vuelve al <a href=\"/\">Orientador</a> y pulsa Seguir por WhatsApp o Dejar mis datos."
    };
    return '<p class="demo-here">' + (labels[active] || "") + "</p>";
  }

  root.USJ = root.USJ || {};
  root.USJ.mountDemoChrome = function (opts) {
    opts = opts || {};
    var active = opts.active || detectActive();
    var mapMount = document.getElementById("demo-map-mount");
    if (mapMount) mapMount.innerHTML = '<div class="demo-map">' + renderDemoMap(active) + "</div>";

    var hereMount = document.getElementById("demo-here-mount");
    if (hereMount) hereMount.innerHTML = hereBanner(active);

    var guideMount = document.getElementById("demo-guide-mount");
    if (guideMount && opts.showGuide) guideMount.innerHTML = renderDemoGuide(active);
  };
})(window);
