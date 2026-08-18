(function () {
  "use strict";

  var state = { answers: {}, step: 0, spec: null, last: null, phase: "intro" };
  var $wizard = document.getElementById("wizard");
  var $intro = document.getElementById("intro-panel");
  var $flow = document.getElementById("flow-panel");
  var $results = document.getElementById("results");
  var $debug = document.getElementById("debug");
  var names = {
    "ai-applied": "IA Aplicada",
    marketing: "Marketing",
    biomechanics: "Biomecánica"
  };

  USJ.track("advisor_started", { flow: "guide" });

  USJ.api("/api/guide").then(function (spec) {
    state.spec = spec;
    renderIntro();
  }).catch(function () {
    $intro.innerHTML = "<div class=\"card\"><p>Vamos a ayudarte a encontrar el programa adecuado.</p><p><a class=\"btn\" href=\"https://www.usj.es/estudios/posgrados/masteres\">Ver másteres USJ</a></p></div>";
  });

  document.getElementById("back").onclick = function () {
    if (!state.spec) return;
    if (state.step === 0) {
      renderIntro();
      return;
    }
    var ids = (state.spec.steps || []).map(function (s) { return s.id; });
    delete state.answers[ids[state.step]];
    state.step -= 1;
    delete state.answers[ids[state.step]];
    $results.classList.remove("visible");
    $flow.hidden = false;
    renderStep();
    refreshRemaining();
  };

  function introCopy() {
    return (state.spec && state.spec.intro_screen) || {};
  }

  function stepHint(step, index) {
    var hints = [
      "Descartamos programas claramente incompatibles con tu titulación.",
      "Filtramos por tu meta profesional. No prometemos empleo ni admisión.",
      "Ajustamos por modalidad según el catálogo, no según la IA."
    ];
    return step.subtitle || hints[index] || "";
  }

  function renderIntro() {
    state.phase = "intro";
    state.answers = {};
    state.step = 0;
    $flow.hidden = true;
    $results.classList.remove("visible");
    $results.innerHTML = "";
    var copy = introCopy();
    var roadmap = (state.spec.steps || []).map(function (s, i) {
      return "<li><span class=\"step-num\">" + (i + 1) + "</span><div><b>" + s.title + "</b><span>" + stepHint(s, i) + "</span></div></li>";
    }).join("");
    $intro.innerHTML =
      "<p class=\"progress\">Cómo funciona</p>" +
      "<h2 class=\"qtitle\">" + (copy.headline || "Encuentra tu máster en 3 pasos") + "</h2>" +
      "<p class=\"lede\">" + (copy.lede || state.spec.intro || "") + "</p>" +
      "<ol class=\"intro-roadmap\">" + roadmap + "</ol>" +
      "<p class=\"lede intro-outcome\">" + (copy.outcome || "") + "</p>" +
      "<button class=\"btn\" id=\"start-guide\" type=\"button\">" + (copy.cta || "Empezar orientación") + "</button>";
    document.getElementById("start-guide").onclick = function () {
      USJ.track("guide_started", { flow: "guide" });
      startFlow();
    };
  }

  function startFlow() {
    state.phase = "step";
    $intro.innerHTML = "";
    $flow.hidden = false;
    renderStep();
    refreshRemaining();
  }

  function renderStep() {
    var steps = state.spec.steps;
    var step = steps[state.step];
    document.getElementById("progress").textContent = "Pregunta " + (state.step + 1) + " de " + steps.length;
    document.getElementById("qtitle").textContent = step.title;
    document.getElementById("qsub").textContent = stepHint(step, state.step);
    var box = document.getElementById("choices");
    box.innerHTML = "";
    step.options.forEach(function (opt) {
      var b = document.createElement("button");
      b.className = "choice";
      b.textContent = opt.label;
      b.onclick = function () { pick(step.id, opt.id); };
      box.appendChild(b);
    });
    document.getElementById("back").hidden = false;
  }

  function pick(stepId, optionId) {
    state.answers[stepId] = optionId;
    USJ.track("priority_selected", { step: stepId, option: optionId });
    if (state.step < state.spec.steps.length - 1) {
      state.step += 1;
      renderStep();
      refreshRemaining();
      return;
    }
    finish();
  }

  function refreshRemaining() {
    USJ.api("/api/guide", {
      method: "POST",
      body: JSON.stringify({ answers: state.answers })
    }).then(function (data) {
      var html = (data.remaining || []).map(function (row) {
        return "<span class=\"remain\">" + (names[row.programme_id] || row.programme) + "</span>";
      }).join("");
      (data.dropped || []).forEach(function (row) {
        html += "<span class=\"remain off\">" + (names[row.programme_id] || row.programme) + "</span>";
      });
      document.getElementById("remaining").innerHTML =
        "<span class=\"remain-count\">Quedan " + (data.remaining || []).length + "</span>" +
        (html || "<span class=\"remain\">3 másteres en juego</span>");
    }).catch(function () {});
  }

  function finish() {
    USJ.track("profile_submitted", { answers: state.answers });
    USJ.api("/api/guide", {
      method: "POST",
      body: JSON.stringify({ answers: state.answers, debug: USJ.debugEnabled() })
    }).then(renderResults).catch(function () {
      renderResults({ fallback: true });
    });
  }

  function pct(row) {
    return row && row.score_pct != null ? row.score_pct : Math.round((row.score || 0) * 100);
  }

  function factsOf(best, limit) {
    var card = best.programme_card || {};
    return (card.approved_facts || []).slice(0, limit || 4);
  }

  function renderResults(payload) {
    USJ.track("recommendation_generated", {
      match: payload.has_strong_match,
      programme: payload.best && payload.best.programme_id
    });
    state.last = payload;
    USJ.saveState({ answers: state.answers, result: payload, signals: { profile_completed: true, recommendation_generated: true } });
    $flow.hidden = true;
    $intro.innerHTML = "";
    $results.classList.add("visible");
    if (payload.fallback || !payload.best) {
      $results.innerHTML = "<div class=\"card\"><h2>Vamos a ayudarte a encontrar el programa adecuado.</h2><p><a class=\"btn\" href=\"https://www.usj.es/estudios/posgrados/masteres\">Ver másteres</a></p><p><button class=\"btn ghost\" id=\"restart\">Empezar de nuevo</button></p></div>";
      document.getElementById("restart").onclick = renderIntro;
      return;
    }
    var best = payload.best;
    var alts = payload.alternatives || [];
    var title = payload.has_strong_match ? "Mejor encaje" : "Opciones más cercanas de este catálogo";
    var facts = factsOf(best, 4);
    $results.innerHTML =
      "<div class=\"result-grid\">" +
        "<article class=\"card\">" +
          "<div class=\"label\">" + title + "</div>" +
          "<p class=\"score\">" + pct(best) + "% de encaje</p>" +
          "<h2 class=\"program-title\">" + best.programme + "</h2>" +
          "<div class=\"meta\"><span class=\"pill\">" + (best.modality_es || best.modality) + "</span><span class=\"pill\">" + best.ects + " ECTS</span><span class=\"eligibility\">" + (best.eligibility || "") + "</span></div>" +
          "<p class=\"label\">Por qué encaja contigo</p>" +
          "<p>" + (best.explanation || "") + "</p>" +
          "<ul class=\"reasons\">" + (best.reasons || []).map(function (r) { return "<li>" + r + "</li>"; }).join("") + "</ul>" +
          (facts.length ? "<p class=\"label\">Qué ofrece este máster</p><ul class=\"reasons facts\">" + facts.map(function (f) { return "<li>" + f + "</li>"; }).join("") + "</ul>" : "") +
          "<div class=\"actions\">" +
            "<button class=\"btn\" id=\"explore\">Explorar este máster</button>" +
            "<button class=\"btn ghost\" id=\"ask\">Preguntar</button>" +
            "<button class=\"btn gold\" id=\"talk\">Seguir por WhatsApp</button>" +
          "</div>" +
          "<div class=\"askbox\" id=\"askbox\"><textarea id=\"q\" placeholder=\"¿Puedo compatibilizarlo con el trabajo?\"></textarea><button class=\"btn ghost\" id=\"askgo\">Enviar pregunta</button><div class=\"answer\" id=\"answer\" hidden></div></div>" +
        "</article>" +
        "<aside class=\"card\">" +
          "<div class=\"label\">Otras opciones que quedan</div>" +
          (alts.length ? alts.map(function (a) {
            return "<div class=\"alt\"><b>" + a.programme + "</b><span>" + pct(a) + "% · " + (a.eligibility || "") + "</span></div>";
          }).join("") : "<p>Solo queda una opción de este catálogo demo.</p>") +
          "<p class=\"footnote\">Catálogo demo: 3 másteres. Un abogado que busca derecho digital no verá un máster jurídico inventado.</p>" +
          "<button class=\"btn ghost\" id=\"restart\">Empezar de nuevo</button>" +
        "</aside>" +
      "</div>";
    document.getElementById("explore").onclick = function () {
      USJ.track("programme_viewed", { id: best.programme_id });
      USJ.clickThrough(best.url);
    };
    document.getElementById("ask").onclick = function () {
      document.getElementById("askbox").classList.add("open");
    };
    document.getElementById("askgo").onclick = askQuestion;
    document.getElementById("restart").onclick = renderIntro;
    document.getElementById("talk").onclick = function () {
      USJ.track("lead_started", { channel: "whatsapp" });
      USJ.openWhatsApp({
        programme: best.programme,
        labels: payload.guide_labels || []
      });
    };
    if (USJ.debugEnabled() && payload.debug) {
      $debug.classList.add("open");
      $debug.textContent = JSON.stringify(payload.debug, null, 2);
    }
  }

  async function askQuestion() {
    var q = (document.getElementById("q").value || "").trim();
    if (!q) return;
    USJ.track("question_asked", { q: q });
    state.questions = (state.questions || []).concat([q]);
    try {
      var res = await USJ.api("/api/question", {
        method: "POST",
        body: JSON.stringify({
          question: q,
          message: (state.last && state.last.guide_labels || []).join(". "),
          recommendation: state.last && state.last.best
        })
      });
      var box = document.getElementById("answer");
      box.hidden = false;
      box.textContent = res.answer;
    } catch (e) {
      var box2 = document.getElementById("answer");
      box2.hidden = false;
      box2.textContent = "Un asesor de USJ puede ayudarte con eso.";
    }
  }
})();
