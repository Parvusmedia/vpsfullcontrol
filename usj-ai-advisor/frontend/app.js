(function () {
  "use strict";

  var state = { answers: {}, step: 0, spec: null, last: null };
  var $wizard = document.getElementById("wizard");
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
    renderStep();
    refreshRemaining();
  }).catch(function () {
    $wizard.innerHTML = "<div class=\"card\"><p>Vamos a ayudarte a encontrar el programa adecuado.</p><p><a class=\"btn\" href=\"https://www.usj.es/estudios/posgrados/masteres\">Ver másteres USJ</a></p></div>";
  });

  document.getElementById("back").onclick = function () {
    if (!state.spec || state.step === 0) return;
    var ids = (state.spec.steps || []).map(function (s) { return s.id; });
    delete state.answers[ids[state.step]];
    state.step -= 1;
    delete state.answers[ids[state.step]];
    $results.classList.remove("visible");
    $wizard.style.display = "";
    renderStep();
    refreshRemaining();
  };

  function renderStep() {
    var steps = state.spec.steps;
    var step = steps[state.step];
    document.getElementById("progress").textContent = "Pregunta " + (state.step + 1) + " de " + steps.length;
    document.getElementById("qtitle").textContent = step.title;
    document.getElementById("qsub").textContent = step.subtitle || "";
    var box = document.getElementById("choices");
    box.innerHTML = "";
    step.options.forEach(function (opt) {
      var b = document.createElement("button");
      b.className = "choice";
      b.textContent = opt.label;
      b.onclick = function () { pick(step.id, opt.id); };
      box.appendChild(b);
    });
    document.getElementById("back").hidden = state.step === 0;
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
      var hold = {};
      (data.remaining || []).forEach(function (row) { hold[row.programme_id] = true; });
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

  function renderResults(payload) {
    USJ.track("recommendation_generated", {
      match: payload.has_strong_match,
      programme: payload.best && payload.best.programme_id
    });
    state.last = payload;
    USJ.saveState({ answers: state.answers, result: payload, signals: { profile_completed: true, recommendation_generated: true } });
    $wizard.style.display = "none";
    $results.classList.add("visible");
    if (payload.fallback || !payload.best) {
      $results.innerHTML = "<div class=\"card\"><h2>Vamos a ayudarte a encontrar el programa adecuado.</h2><p><a class=\"btn\" href=\"https://www.usj.es/estudios/posgrados/masteres\">Ver másteres</a></p><p><button class=\"btn ghost\" id=\"restart\">Empezar de nuevo</button></p></div>";
      document.getElementById("restart").onclick = restart;
      return;
    }
    var best = payload.best;
    var alts = payload.alternatives || [];
    var title = payload.has_strong_match ? "Mejor encaje" : "Opciones más cercanas de este catálogo";
    $results.innerHTML =
      "<div class=\"result-grid\">" +
        "<article class=\"card\">" +
          "<div class=\"label\">" + title + "</div>" +
          "<p class=\"score\">" + pct(best) + "% de encaje</p>" +
          "<h2 class=\"program-title\">" + best.programme + "</h2>" +
          "<div class=\"meta\"><span class=\"pill\">" + (best.modality_es || best.modality) + "</span><span class=\"pill\">" + best.ects + " ECTS</span><span class=\"eligibility\">" + (best.eligibility || "") + "</span></div>" +
          "<p>" + (best.explanation || "") + "</p>" +
          "<p class=\"label\">Por qué encaja</p>" +
          "<ul class=\"reasons\">" + (best.reasons || []).map(function (r) { return "<li>" + r + "</li>"; }).join("") + "</ul>" +
          "<div class=\"actions\">" +
            "<button class=\"btn\" id=\"explore\">Explorar este máster</button>" +
            "<button class=\"btn ghost\" id=\"ask\">Preguntar</button>" +
            "<button class=\"btn gold\" id=\"talk\">Hablar con un asesor</button>" +
          "</div>" +
          "<div class=\"askbox\" id=\"askbox\"><textarea id=\"q\" placeholder=\"¿Puedo compatibilizarlo con el trabajo?\"></textarea><button class=\"btn ghost\" id=\"askgo\">Enviar pregunta</button><div class=\"answer\" id=\"answer\" hidden></div></div>" +
          "<div class=\"lead\" id=\"leadform\"></div>" +
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
    document.getElementById("restart").onclick = restart;
    wireLead();
    if (USJ.debugEnabled() && payload.debug) {
      $debug.classList.add("open");
      $debug.textContent = JSON.stringify(payload.debug, null, 2);
    }
  }

  function restart() {
    state.answers = {};
    state.step = 0;
    state.last = null;
    $results.classList.remove("visible");
    $results.innerHTML = "";
    $wizard.style.display = "";
    $debug.classList.remove("open");
    renderStep();
    refreshRemaining();
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

  function wireLead() {
    var talk = document.getElementById("talk");
    if (!talk) return;
    talk.onclick = function () {
      USJ.track("lead_started");
      var form = document.getElementById("leadform");
      form.classList.add("open");
      form.innerHTML =
        "<input id=\"n\" placeholder=\"Nombre\" autocomplete=\"name\">" +
        "<input id=\"e\" placeholder=\"Email\" type=\"email\" autocomplete=\"email\">" +
        "<input id=\"p\" placeholder=\"Teléfono\" autocomplete=\"tel\">" +
        "<button class=\"btn gold\" id=\"sendlead\">Enviar a admisiones</button>" +
        "<p class=\"footnote\" id=\"leadmsg\"></p>";
      document.getElementById("sendlead").onclick = sendLead;
    };
  }

  async function sendLead() {
    var rec = state.last || {};
    try {
      var out = await USJ.api("/api/lead", {
        method: "POST",
        body: JSON.stringify({
          name: document.getElementById("n").value,
          email: document.getElementById("e").value,
          phone: document.getElementById("p").value,
          profile: rec.profile || {},
          recommendation: rec.best,
          alternatives: rec.alternatives || [],
          questions_asked: state.questions || [],
          signals: { lead_submitted: true, programme_viewed: true }
        })
      });
      USJ.track("lead_submitted", { intent: out.lead_intent });
      document.getElementById("leadmsg").textContent = "Contexto enviado. Intención " + out.lead_intent + ". Ábrelo en Admisiones.";
    } catch (e) {
      document.getElementById("leadmsg").textContent = "Vamos a ayudarte a encontrar el programa adecuado.";
    }
  }
})();
