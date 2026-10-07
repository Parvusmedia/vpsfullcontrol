(function () {
  "use strict";

  var state = { answers: {}, step: 0, spec: null, last: null, phase: "intro" };
  var $wizard = document.getElementById("wizard");
  var $intro = document.getElementById("intro-panel");
  var $flow = document.getElementById("flow-panel");
  var $results = document.getElementById("results");
  var $debug = document.getElementById("debug");
  var names = {
    "ai-applied": "Applied AI",
    marketing: "Marketing",
    biomechanics: "Biomechanics"
  };

  EDU.track("advisor_started", { flow: "guide" });

  EDU.api("/api/guide").then(function (spec) {
    state.spec = spec;
    if (EDU.scenarioParam() === "lawyer") {
      state.answers = { background: "law", goal: "tech-law", format: "work-study" };
      finish();
      return;
    }
    renderIntro();
  }).catch(function () {
    $intro.innerHTML = "<div class=\"card\"><p>We will help you find the right programme.</p><p><a class=\"btn\" href=\"https://educationdemo.pmediaplus.com/programmes\">View EDU programmes</a></p></div>";
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
      "We filter out programmes clearly incompatible with your degree.",
      "We narrow by your career goal and help you orient better.",
      "We adjust by study mode from the catalogue, not from AI."
    ];
    return step.subtitle || hints[index] || "";
  }

  function updateStepProgress() {
    var bar = document.getElementById("step-progress");
    if (!bar) return;
    var segments = bar.querySelectorAll("i");
    for (var i = 0; i < segments.length; i++) {
      segments[i].classList.toggle("on", state.phase === "step" && i <= state.step);
    }
  }

  function animateFlow() {
    $flow.classList.remove("flow-enter");
    void $flow.offsetWidth;
    $flow.classList.add("flow-enter");
  }

  function nextStepBanner() {
    var href = EDU.appendPresent ? EDU.appendPresent("/ad/") : "/ad/";
    return (
      '<div class="demo-next-banner">' +
      '<p class="kicker">Next · step 2</p>' +
      "<p><b>Interactive ad</b> — the same advisor inside the display creative.</p>" +
      '<a class="btn" href="' + href + '">See live example →</a>' +
      "</div>"
    );
  }

  function renderIntro() {
    state.phase = "intro";
    state.answers = {};
    state.step = 0;
    $flow.hidden = true;
    $results.classList.remove("visible");
    $results.innerHTML = "";
    updateStepProgress();
    var copy = introCopy();
    var roadmap = (state.spec.steps || []).map(function (s, i) {
      return "<li><span class=\"step-num\">" + (i + 1) + "</span><div><b>Question " + (i + 1) + " · " + s.title + "</b><span>" + stepHint(s, i) + "</span></div></li>";
    }).join("");
    $intro.innerHTML =
      "<p class=\"progress\">How it works</p>" +
      "<h2 class=\"qtitle\">" + (copy.headline || "Find your programme in 3 questions") + "</h2>" +
      "<p class=\"lede\">" + (copy.lede || state.spec.intro || "") + "</p>" +
      "<ol class=\"intro-roadmap\">" + roadmap + "</ol>" +
      "<p class=\"lede intro-outcome\">" + (copy.outcome || "") + "</p>" +
      "<button class=\"btn\" id=\"start-guide\" type=\"button\">" + (copy.cta || "Start advising") + "</button>";
    document.getElementById("start-guide").onclick = function () {
      EDU.track("guide_started", { flow: "guide" });
      startFlow();
    };
  }

  function startFlow() {
    state.phase = "step";
    $intro.innerHTML = "";
    $flow.hidden = false;
    renderStep();
    refreshRemaining();
    EDU.prefetch("/ad/unit.html?size=300x600");
  }

  function renderStep() {
    var steps = state.spec.steps;
    var step = steps[state.step];
    document.getElementById("progress").textContent = "Question " + (state.step + 1) + " of " + steps.length;
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
    updateStepProgress();
    animateFlow();
  }

  function pick(stepId, optionId) {
    state.answers[stepId] = optionId;
    EDU.track("priority_selected", { step: stepId, option: optionId });
    if (state.step < state.spec.steps.length - 1) {
      state.step += 1;
      renderStep();
      refreshRemaining();
      return;
    }
    finish();
  }

  function refreshRemaining() {
    EDU.api("/api/guide", {
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
        "<span class=\"remain-count\">" + (data.remaining || []).length + " left</span>" +
        (html || "<span class=\"remain\">3 programmes in play</span>");
    }).catch(function () {});
  }

  function finish() {
    EDU.track("profile_submitted", { answers: state.answers });
    EDU.api("/api/guide", {
      method: "POST",
      body: JSON.stringify({ answers: state.answers, debug: EDU.debugEnabled() })
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

  function bindLeadForm(payload) {
    var leadBtn = document.getElementById("lead");
    var leadbox = document.getElementById("leadbox");
    if (!leadBtn || !leadbox) return;
    leadBtn.onclick = function () {
      EDU.track("lead_started", { channel: "form", surface: "orientador" });
      leadbox.classList.add("open");
      leadBtn.hidden = true;
    };
    document.getElementById("leadsend").onclick = function () {
      var name = (document.getElementById("lname").value || "").trim();
      var email = (document.getElementById("lemail").value || "").trim();
      if (!name || !email) return;
      var phone = (document.getElementById("lphone").value || "").trim();
      EDU.submitLead({
        name: name,
        email: email,
        phone: phone,
        profile: payload.profile || { answers: state.answers, parser: "guide" },
        recommendation: payload.best,
        alternatives: payload.alternatives || [],
        questions_asked: state.questions || [],
        priority: (payload.guide_labels || []).join(" · "),
        signals: { lead_submitted: true, from_orientador: true }
      }).then(function () {
        document.getElementById("leadok").hidden = false;
        document.getElementById("leadsend").disabled = true;
        EDU.track("lead_submitted", { surface: "orientador" });
      }).catch(function () {
        document.getElementById("leadok").textContent = "Could not send. Try WhatsApp instead.";
        document.getElementById("leadok").hidden = false;
      });
    };
  }

  function renderResults(payload) {
    EDU.track("recommendation_generated", {
      match: payload.has_strong_match,
      programme: payload.best && payload.best.programme_id
    });
    state.last = payload;
    EDU.saveState({ answers: state.answers, result: payload, signals: { profile_completed: true, recommendation_generated: true } });
    $flow.hidden = true;
    $intro.innerHTML = "";
    $results.classList.add("visible");
    updateStepProgress();
    if ($debug) {
      $debug.classList.remove("open");
      $debug.textContent = "";
    }
    if (payload.fallback || !payload.best) {
      $results.innerHTML = "<div class=\"card\"><h2>We will help you find the right programme.</h2><p><a class=\"btn\" href=\"https://educationdemo.pmediaplus.com/programmes\">View programmes</a></p><p><button class=\"btn ghost\" id=\"restart\">Start over</button></p></div>";
      document.getElementById("restart").onclick = renderIntro;
      return;
    }
    var best = payload.best;
    var alts = payload.alternatives || [];
    var title = payload.has_strong_match ? "Best fit" : "Closest options in this catalogue";
    var facts = factsOf(best, 4);
    $results.innerHTML =
      nextStepBanner() +
      "<div class=\"result-grid\">" +
        "<article class=\"card\">" +
          "<div class=\"label\">" + title + "</div>" +
          "<p class=\"score\">" + pct(best) + "% fit</p>" +
          "<h2 class=\"program-title\">" + best.programme + "</h2>" +
          "<div class=\"meta\"><span class=\"pill\">" + (best.modality_es || best.modality) + "</span><span class=\"pill\">" + best.ects + " ECTS</span><span class=\"eligibility\">" + (best.eligibility || "") + "</span></div>" +
          "<p class=\"label\">Why it fits you</p>" +
          "<p>" + (best.explanation || "") + "</p>" +
          "<ul class=\"reasons\">" + (best.reasons || []).map(function (r) { return "<li>" + r + "</li>"; }).join("") + "</ul>" +
          (facts.length ? "<p class=\"label\">What this programme offers</p><ul class=\"reasons facts\">" + facts.map(function (f) { return "<li>" + f + "</li>"; }).join("") + "</ul>" : "") +
          "<div class=\"actions\">" +
            "<button class=\"btn\" id=\"explore\">Explore this programme</button>" +
            "<button class=\"btn ghost\" id=\"ask\">Ask a question</button>" +
            "<button class=\"btn gold\" id=\"talk\">Continue on WhatsApp</button>" +
            "<button class=\"btn ghost\" id=\"lead\">Leave my details</button>" +
          "</div>" +
          "<div class=\"lead\" id=\"leadbox\">" +
            "<input type=\"text\" id=\"lname\" placeholder=\"Name\" autocomplete=\"name\">" +
            "<input type=\"email\" id=\"lemail\" placeholder=\"Email\" autocomplete=\"email\">" +
            "<input type=\"tel\" id=\"lphone\" placeholder=\"Phone (optional)\" autocomplete=\"tel\">" +
            "<button class=\"btn\" id=\"leadsend\" type=\"button\">Send</button>" +
            "<p class=\"lead-ok\" id=\"leadok\" hidden>Thank you. An EDU advisor will contact you.</p>" +
          "</div>" +
          "<div class=\"askbox\" id=\"askbox\"><textarea id=\"q\" placeholder=\"Can I balance it with work?\"></textarea><button class=\"btn ghost\" id=\"askgo\">Send question</button><div class=\"answer\" id=\"answer\" hidden></div></div>" +
        "</article>" +
        "<aside class=\"card\">" +
          "<div class=\"label\">Other options still available</div>" +
          (alts.length ? alts.map(function (a) {
            return "<div class=\"alt\"><b>" + a.programme + "</b><span>" + pct(a) + "% · " + (a.eligibility || "") + "</span></div>";
          }).join("") : "<p>Only one option remains available.</p>") +
          "<button class=\"btn ghost\" id=\"restart\">Start over</button>" +
        "</aside>" +
      "</div>";
    document.getElementById("explore").onclick = function () {
      EDU.track("programme_viewed", { id: best.programme_id });
      EDU.clickThrough(best.url);
    };
    document.getElementById("ask").onclick = function () {
      document.getElementById("askbox").classList.add("open");
    };
    document.getElementById("askgo").onclick = askQuestion;
    document.getElementById("restart").onclick = renderIntro;
    document.getElementById("talk").onclick = function () {
      EDU.track("lead_started", { channel: "whatsapp" });
      EDU.openWhatsApp({
        programme: best.programme,
        labels: payload.guide_labels || []
      });
    };
    bindLeadForm(payload);
    if (EDU.debugEnabled() && payload.debug && $debug) {
      $debug.classList.add("open");
      $debug.textContent = JSON.stringify(payload.debug, null, 2);
    }
    EDU.prefetch("/ad");
  }

  async function askQuestion() {
    var q = (document.getElementById("q").value || "").trim();
    if (!q) return;
    EDU.track("question_asked", { q: q });
    state.questions = (state.questions || []).concat([q]);
    try {
      var res = await EDU.api("/api/question", {
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
      box2.textContent = "An EDU advisor can help you with that.";
    }
  }
})();
