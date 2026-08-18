(function () {
  "use strict";

  var state = USJ.loadState();
  var $story = document.getElementById("story");
  var $examples = document.getElementById("examples");
  var $results = document.getElementById("results");
  var $loading = document.getElementById("loading");
  var $debug = document.getElementById("debug");

  USJ.examples.forEach(function (ex) {
    var b = document.createElement("button");
    b.className = "chip";
    b.textContent = ex.label;
    b.onclick = function () {
      $story.value = ex.text;
      $story.focus();
    };
    $examples.appendChild(b);
  });

  document.getElementById("find").addEventListener("click", submit);
  $story.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
  });

  function sleep(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  }

  async function submit() {
    var message = ($story.value || "").trim();
    if (message.length < 8) {
      $story.focus();
      return;
    }
    USJ.track("profile_submitted", { chars: message.length });
    document.getElementById("start").style.display = "none";
    $results.classList.remove("visible");
    $loading.classList.add("visible");
    ["step1", "step2", "step3"].forEach(function (id) {
      document.getElementById(id).classList.remove("on");
    });
    document.getElementById("step1").classList.add("on");
    await sleep(380);
    document.getElementById("step2").classList.add("on");
    var payload;
    try {
      payload = await USJ.api("/api/recommend", {
        method: "POST",
        body: JSON.stringify({
          message: message,
          priority: state.priority || null,
          debug: USJ.debugEnabled()
        })
      });
    } catch (err) {
      payload = { fallback: true, has_strong_match: false };
    }
    await sleep(320);
    document.getElementById("step3").classList.add("on");
    await sleep(280);
    $loading.classList.remove("visible");
    state.message = message;
    state.result = payload;
    state.signals = Object.assign({}, state.signals, {
      profile_completed: true,
      recommendation_generated: true
    });
    USJ.saveState(state);
    USJ.track("recommendation_generated", {
      match: payload.has_strong_match,
      programme: payload.best && payload.best.programme_id
    });
    render(payload);
  }

  function pct(row) {
    return (row && (row.score_pct != null)) ? row.score_pct : Math.round((row.score || 0) * 100);
  }

  function render(payload) {
    $results.classList.add("visible");
    if (payload.fallback) {
      $results.innerHTML = '<div class="card nomatch"><h2>Let\'s help you find the right programme.</h2><p>The advisor is temporarily unavailable. You can still explore the official catalogue.</p><p><a class="btn" href="https://www.usj.es/estudios/posgrados/masteres" target="_blank" rel="noopener">Explore programmes</a></p></div>';
      return;
    }
    if (!payload.has_strong_match) {
      $results.innerHTML = '<div class="card nomatch"><div class="kicker">No forced match</div><h2>We couldn’t find a strong match among these programmes.</h2><p>An USJ advisor may be able to help you explore other options.</p><div class="actions"><button class="btn gold" id="talk">Talk to an advisor</button></div><div class="lead" id="leadform"></div></div>';
      wireLead();
      return;
    }
    var best = payload.best;
    var alts = payload.alternatives || [];
    $results.innerHTML =
      '<div class="result-grid">' +
        '<article class="card">' +
          '<div class="label">Your best match</div>' +
          '<p class="score">' + pct(best) + '% match</p>' +
          '<h2 class="program-title">' + best.programme + '</h2>' +
          '<div class="meta"><span class="pill">' + best.modality + '</span><span class="pill">' + best.ects + ' ECTS</span><span class="eligibility">' + (best.eligibility || "") + '</span></div>' +
          '<p>' + (best.explanation || "") + '</p>' +
          '<p class="label">Why it fits you</p>' +
          '<ul class="reasons">' + (best.reasons || []).map(function (r) { return "<li>" + r + "</li>"; }).join("") + "</ul>" +
          '<div class="actions">' +
            '<button class="btn" id="explore">Explore this master</button>' +
            '<button class="btn ghost" id="ask">Ask a question</button>' +
            '<button class="btn gold" id="talk">Talk to an advisor</button>' +
          "</div>" +
          '<div class="askbox" id="askbox"><textarea id="q" placeholder="Can I combine it with work?"></textarea><button class="btn ghost" id="askgo">Send question</button><div class="answer" id="answer" hidden></div></div>' +
          '<div class="priority"><p class="label">What’s most important to you?</p><div class="chips" id="prios"></div></div>' +
          '<div class="lead" id="leadform"></div>' +
        "</article>" +
        '<aside class="card">' +
          '<div class="label">Other possible matches</div>' +
          alts.map(function (a) {
            return '<div class="alt"><b>' + a.programme + '</b><span>' + pct(a) + '% match</span></div>';
          }).join("") +
        "</aside>" +
      "</div>";

    document.getElementById("explore").onclick = function () {
      USJ.track("programme_viewed", { id: best.programme_id });
      state.signals.programme_viewed = true;
      USJ.saveState(state);
      USJ.clickThrough(best.url);
    };
    document.getElementById("ask").onclick = function () {
      document.getElementById("askbox").classList.add("open");
    };
    document.getElementById("askgo").onclick = askQuestion;
    var prios = document.getElementById("prios");
    USJ.priorities.forEach(function (p) {
      var b = document.createElement("button");
      b.className = "chip";
      b.textContent = p;
      if (state.priority === p) b.style.borderColor = "var(--gold)";
      b.onclick = function () {
        state.priority = p;
        state.signals.priority_selected = true;
        USJ.saveState(state);
        USJ.track("priority_selected", { priority: p });
        $story.value = state.message;
        submit();
      };
      prios.appendChild(b);
    });
    wireLead();
    if (USJ.debugEnabled() && payload.debug) {
      $debug.classList.add("open");
      $debug.textContent = JSON.stringify({
        profile: payload.profile,
        scores: payload.debug.all_scores,
        weights: payload.debug.weights
      }, null, 2);
    }
  }

  async function askQuestion() {
    var q = (document.getElementById("q").value || "").trim();
    if (!q) return;
    USJ.track("question_asked", { q: q });
    state.questions = (state.questions || []).concat([q]);
    state.signals.question_asked = true;
    USJ.saveState(state);
    try {
      var res = await USJ.api("/api/question", {
        method: "POST",
        body: JSON.stringify({
          question: q,
          message: state.message,
          priority: state.priority || null,
          recommendation: state.result && state.result.best
        })
      });
      var box = document.getElementById("answer");
      box.hidden = false;
      box.textContent = res.answer;
    } catch (e) {
      var box2 = document.getElementById("answer");
      box2.hidden = false;
      box2.textContent = "An USJ advisor can help with that.";
    }
  }

  function wireLead() {
    var talk = document.getElementById("talk");
    if (!talk) return;
    talk.onclick = function () {
      USJ.track("lead_started");
      state.signals.lead_started = true;
      USJ.saveState(state);
      var form = document.getElementById("leadform");
      form.classList.add("open");
      form.innerHTML =
        '<input id="n" placeholder="Name" autocomplete="name">' +
        '<input id="e" placeholder="Email" type="email" autocomplete="email">' +
        '<input id="p" placeholder="Phone" autocomplete="tel">' +
        '<button class="btn gold" id="sendlead">Send to admissions</button>' +
        '<p class="footnote" id="leadmsg"></p>';
      document.getElementById("sendlead").onclick = sendLead;
    };
  }

  async function sendLead() {
    var rec = state.result || {};
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
          priority: state.priority || null,
          signals: state.signals || {}
        })
      });
      USJ.track("lead_submitted", { intent: out.lead_intent });
      document.getElementById("leadmsg").textContent = "Context sent. Intent " + out.lead_intent + ". Open Admissions to see the prospect.";
    } catch (e) {
      document.getElementById("leadmsg").textContent = "Let’s help you find the right programme. Please try again or explore the catalogue.";
    }
  }
})();
