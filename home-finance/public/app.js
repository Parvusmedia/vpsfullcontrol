/* Hogar Finanzas — single-user dashboard */
(function () {
  const TOKEN_KEY = "home_finance_token";
  const MAP_KEY = "home_finance_column_map";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  let categories = [];
  let rules = [];
  let allTransactions = [];
  let parsedRows = [];
  let parsedHeaders = [];
  let charts = {};
  let budgets = {};
  let fixedCategories = [];
  const REMINDER_KEY = "home_finance_reminder_dismiss";

  function token() {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  }

  function setToken(t) {
    sessionStorage.setItem(TOKEN_KEY, t);
  }

  function clearToken() {
    sessionStorage.removeItem(TOKEN_KEY);
  }

  async function api(path, opts = {}) {
    const headers = { ...(opts.headers || {}) };
    if (token()) headers["X-Home-Token"] = token();
    if (opts.body && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(path, { ...opts, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || "request_failed"), { status: res.status, data });
    return data;
  }

  function currentMonth() {
    const el = $("#month-select");
    if (el && el.value) return el.value;
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function setDefaultMonth() {
    const el = $("#month-select");
    if (el) el.value = currentMonth();
    syncYearFromMonth();
  }

  function syncYearFromMonth() {
    const ysel = $("#year-select");
    if (!ysel) return;
    const y = currentMonth().slice(0, 4);
    if (!ysel.querySelector(`option[value="${y}"]`)) {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      ysel.appendChild(opt);
    }
    ysel.value = y;
  }

  function fillYearSelect() {
    const ysel = $("#year-select");
    if (!ysel) return;
    const years = new Set(allTransactions.map((t) => (t.month || "").slice(0, 4)).filter(Boolean));
    const cy = new Date().getFullYear();
    years.add(String(cy));
    years.add(String(cy - 1));
    ysel.innerHTML = [...years].sort().map((y) => `<option value="${y}">${y}</option>`).join("");
    syncYearFromMonth();
  }

  function activeTagFilter() {
    const dash = ($("#filter-tag")?.value || "").trim().toLowerCase();
    const mov = ($("#filter-tag-movements")?.value || "").trim().toLowerCase();
    return dash || mov;
  }

  function txHasTag(tx, tag) {
    if (!tag) return true;
    const tags = (tx.tags || []).map((t) => String(t).toLowerCase());
    return tags.some((t) => t.includes(tag) || t.replace(/^#/, "").includes(tag));
  }

  function filterTxs(list) {
    const tag = activeTagFilter();
    if (tag) list = list.filter((t) => txHasTag(t, tag));
    return list;
  }

  function formatEur(n) {
    return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(n);
  }

  function parseAmount(raw) {
    if (typeof raw === "number") return raw;
    let s = String(raw ?? "").trim();
    if (!s) return 0;
    s = s.replace(/\s/g, "").replace(/€/g, "");
    if (s.includes(",") && s.includes(".")) {
      s = s.replace(/\./g, "").replace(",", ".");
    } else if (s.includes(",")) {
      s = s.replace(",", ".");
    }
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : 0;
  }

  function parseDate(raw) {
    const s = String(raw ?? "").trim();
    if (!s) return "";
    if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
    const dmy = s.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/);
    if (dmy) {
      const dd = dmy[1].padStart(2, "0");
      const mm = dmy[2].padStart(2, "0");
      let yy = dmy[3];
      if (yy.length === 2) yy = "20" + yy;
      return `${yy}-${mm}-${dd}`;
    }
    const excel = Date.parse(s);
    if (!Number.isNaN(excel)) {
      const d = new Date(excel);
      return d.toISOString().slice(0, 10);
    }
    return "";
  }

  function guessHeader(headers, patterns) {
    const lower = headers.map((h) => String(h).toLowerCase());
    for (const [key, words] of Object.entries(patterns)) {
      const idx = lower.findIndex((h) => words.some((w) => h.includes(w)));
      if (idx >= 0) return headers[idx];
    }
    return "";
  }

  function buildMapOptions(headers) {
    const patterns = {
      date: ["fecha", "date", "f. valor", "f valor", "fecha valor", "booking date", "data"],
      concept: ["concepto", "descripcion", "descripción", "detail", "merchant", "beneficiario", "movimiento", "concepto de la operación", "información adicional"],
      amount: ["importe", "amount", "cantidad", "saldo", "importe total"],
      debit: ["cargo", "debe", "debit", "importe cargo", "gastos"],
      credit: ["abono", "haber", "credit", "importe abono", "ingresos"],
      category: ["categoria", "categoría", "category"],
      account: ["cuenta", "account", "tarjeta", "iban", "producto"],
    };
    const saved = JSON.parse(localStorage.getItem(MAP_KEY) || "{}");
    const pick = (key, words) => saved[key] || guessHeader(headers, { [key]: words });
    return {
      date: pick("date", patterns.date),
      concept: pick("concept", patterns.concept),
      amount: pick("amount", patterns.amount),
      debit: pick("debit", patterns.debit),
      credit: pick("credit", patterns.credit),
      category: pick("category", patterns.category),
      account: pick("account", patterns.account),
    };
  }

  function resolveAmount(row, map) {
    if (map.amount) {
      const v = parseAmount(row[map.amount]);
      if (v !== 0) return v;
    }
    const debit = map.debit ? parseAmount(row[map.debit]) : 0;
    const credit = map.credit ? parseAmount(row[map.credit]) : 0;
    if (debit !== 0 || credit !== 0) {
      if (debit !== 0 && credit === 0) return -Math.abs(debit);
      if (credit !== 0 && debit === 0) return Math.abs(credit);
      return credit - debit;
    }
    return 0;
  }

  function rowsToTransactions(rows, map) {
    return rows
      .map((row) => {
        const date = parseDate(row[map.date]);
        const concept = String(row[map.concept] ?? "").trim();
        const amount = resolveAmount(row, map);
        const category = map.category ? String(row[map.category] ?? "").trim() : "";
        const account = map.account ? String(row[map.account] ?? "").trim() : "";
        if (!date || !concept) return null;
        if (!map.amount && !map.debit && !map.credit) return null;
        if (amount === 0 && !map.amount) return null;
        return {
          date,
          concept,
          amount,
          category,
          account,
          tags: [],
        };
      })
      .filter(Boolean);
  }

  function showGate(msg) {
    document.body.classList.remove("is-authed");
    const gate = $("#gate");
    const app = $("#app");
    gate.hidden = false;
    gate.classList.add("is-visible");
    gate.setAttribute("aria-hidden", "false");
    app.hidden = true;
    app.classList.remove("is-visible");
    app.setAttribute("aria-hidden", "true");
    const err = $("#gate-error");
    if (msg) {
      err.textContent = msg;
      err.hidden = false;
    } else {
      err.hidden = true;
    }
    $("#gate-token")?.focus();
  }

  function showApp() {
    document.body.classList.add("is-authed");
    const gate = $("#gate");
    const app = $("#app");
    gate.hidden = true;
    gate.classList.remove("is-visible");
    gate.setAttribute("aria-hidden", "true");
    const form = $("#gate-form");
    if (form) form.reset();
    app.hidden = false;
    app.classList.add("is-visible");
    app.setAttribute("aria-hidden", "false");
  }

  async function bootstrap() {
    try {
      const health = await fetch("/api/health").then((r) => r.json()).catch(() =>
        fetch("/api/health.php").then((r) => r.json())
      );
      if (!health.configured) {
        showGate("El servidor aún no está configurado (HOME_FINANCE_API_TOKEN).");
        return;
      }
    } catch {
      showGate("No se pudo contactar con la API.");
      return;
    }

    if (!token()) {
      showGate();
      return;
    }

    try {
      await loadStore();
      await refreshTransactions();
      showApp();
      renderAll();
    } catch (e) {
      if (e.status === 401) {
        clearToken();
        showGate("Clave incorrecta.");
      } else {
        showGate("Error al cargar datos.");
      }
    }
  }

  async function loadStore() {
    const data = await api("/api/store.php");
    categories = data.categories || [];
    rules = data.rules || [];
    budgets = data.budgets || {};
    fixedCategories = data.fixed_categories || [];
    fillCategorySelects();
    renderRules();
    renderBudgetForm();
    renderFixedCategories();
  }

  async function refreshTransactions() {
    const data = await api("/api/transactions.php");
    allTransactions = data.transactions || [];
    fillYearSelect();
  }

  function txsForMonth(month) {
    return allTransactions.filter((t) => t.month === month);
  }

  function prevMonth(month) {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m - 2, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function isExpenseTx(t) {
    return t.type !== "ingreso" && t.type !== "transferencia" && t.amount < 0;
  }

  function sumExpenses(txs) {
    return filterTxs(txs).filter(isExpenseTx).reduce((s, t) => s + Math.abs(t.amount), 0);
  }

  function sumIncome(txs) {
    return filterTxs(txs)
      .filter((t) => t.type === "ingreso" || (t.amount > 0 && t.type !== "transferencia"))
      .reduce((s, t) => s + Math.abs(t.amount), 0);
  }

  function sumFixedVariable(txs) {
    const exp = filterTxs(txs).filter(isExpenseTx);
    let fixed = 0;
    let variable = 0;
    exp.forEach((t) => {
      const amt = Math.abs(t.amount);
      if (fixedCategories.includes(t.category)) fixed += amt;
      else variable += amt;
    });
    return { fixed, variable };
  }

  function sumYearExpenses(year) {
    return sumExpenses(allTransactions.filter((t) => (t.month || "").startsWith(year + "-")));
  }

  function renderReminder() {
    const el = $("#monthly-reminder");
    if (!el) return;
    const month = currentMonth();
    const dismissed = localStorage.getItem(REMINDER_KEY);
    const hasData = txsForMonth(month).length > 0;
    if (hasData || dismissed === month) {
      el.hidden = true;
      return;
    }
    el.hidden = false;
    el.innerHTML = `<span>¿Ya subiste el extracto de <strong>${month}</strong>?</span>
      <button type="button" class="btn btn-secondary btn-sm" data-go-import>Ir a Importar</button>
      <button type="button" class="btn btn-ghost btn-sm" data-dismiss-reminder>Ocultar este mes</button>`;
    el.querySelector("[data-go-import]")?.addEventListener("click", () => {
      $$(".tab").find((t) => t.dataset.tab === "import")?.click();
    });
    el.querySelector("[data-dismiss-reminder]")?.addEventListener("click", () => {
      localStorage.setItem(REMINDER_KEY, month);
      el.hidden = true;
    });
  }

  function renderKpis() {
    const month = currentMonth();
    const year = month.slice(0, 4);
    const cur = filterTxs(txsForMonth(month));
    const prev = filterTxs(txsForMonth(prevMonth(month)));
    const expenses = sumExpenses(cur);
    const income = sumIncome(cur);
    const prevExp = sumExpenses(prev);
    const delta = prevExp > 0 ? ((expenses - prevExp) / prevExp) * 100 : 0;
    const unclassified = cur.filter((t) => t.category === "Otros" && t.amount < 0).length;
    const days = new Date(month + "-01");
    const dim = new Date(days.getFullYear(), days.getMonth() + 1, 0).getDate();
    const daily = expenses / dim;
    const { fixed, variable } = sumFixedVariable(cur);
    const yearExp = sumYearExpenses(year);

    $("#kpi-grid").innerHTML = `
      <div class="kpi"><div class="kpi-label">Gastos del mes</div><div class="kpi-value negative">${formatEur(expenses)}</div></div>
      <div class="kpi"><div class="kpi-label">Ingresos</div><div class="kpi-value positive">${formatEur(income)}</div></div>
      <div class="kpi"><div class="kpi-label">Balance</div><div class="kpi-value ${income - expenses >= 0 ? "positive" : "negative"}">${formatEur(income - expenses)}</div></div>
      <div class="kpi"><div class="kpi-label">Gastos fijos</div><div class="kpi-value">${formatEur(fixed)}</div><div class="kpi-sub">vs variable ${formatEur(variable)}</div></div>
      <div class="kpi"><div class="kpi-label">Año ${year}</div><div class="kpi-value negative">${formatEur(yearExp)}</div><div class="kpi-sub">gastos acumulados</div></div>
      <div class="kpi"><div class="kpi-label">vs mes anterior</div><div class="kpi-value">${delta >= 0 ? "+" : ""}${delta.toFixed(1)}%</div><div class="kpi-sub">en gastos</div></div>
      <div class="kpi"><div class="kpi-label">Media / día</div><div class="kpi-value">${formatEur(daily)}</div></div>
      <div class="kpi"><div class="kpi-label">Sin clasificar</div><div class="kpi-value">${unclassified}</div><div class="kpi-sub">categoría Otros</div></div>
    `;
    renderReminder();
  }

  function destroyChart(id) {
    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }
  }

  function renderCharts() {
    const month = currentMonth();
    const cur = filterTxs(txsForMonth(month)).filter(isExpenseTx);

    const byCat = {};
    cur.forEach((t) => {
      const c = t.category || "Otros";
      byCat[c] = (byCat[c] || 0) + Math.abs(t.amount);
    });
    const catLabels = Object.keys(byCat).sort((a, b) => byCat[b] - byCat[a]);
    const catData = catLabels.map((k) => byCat[k]);

    destroyChart("cat");
    charts.cat = new Chart($("#chart-categories"), {
      type: "doughnut",
      data: {
        labels: catLabels,
        datasets: [{ data: catData, backgroundColor: ["#3dd6c3", "#5c9ead", "#e9c46a", "#f4a261", "#e76f51", "#8ab17d", "#b8b8ff", "#ffd6a5", "#9bf6ff", "#bdb2ff"] }],
      },
      options: { plugins: { legend: { position: "bottom", labels: { color: "#8fa3b8" } } } },
    });

    const byMerchant = {};
    cur.forEach((t) => {
      const key = t.concept.slice(0, 40);
      byMerchant[key] = (byMerchant[key] || 0) + Math.abs(t.amount);
    });
    const merchants = Object.entries(byMerchant).sort((a, b) => b[1] - a[1]).slice(0, 8);

    destroyChart("merch");
    charts.merch = new Chart($("#chart-merchants"), {
      type: "bar",
      data: {
        labels: merchants.map((m) => m[0]),
        datasets: [{ label: "€", data: merchants.map((m) => m[1]), backgroundColor: "#3dd6c3" }],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
          y: { ticks: { color: "#8fa3b8", font: { size: 10 } }, grid: { display: false } },
        },
      },
    });

    const months = [];
    const [y, m] = month.split("-").map(Number);
    for (let i = 11; i >= 0; i--) {
      const d = new Date(y, m - 1 - i, 1);
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }
    const trend = months.map((mo) => sumExpenses(txsForMonth(mo)));

    destroyChart("trend");
    charts.trend = new Chart($("#chart-trend"), {
      type: "line",
      data: {
        labels: months,
        datasets: [{ label: "Gastos", data: trend, borderColor: "#3dd6c3", tension: 0.3, fill: false }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#8fa3b8", maxRotation: 45 }, grid: { color: "#2f3d4f" } },
          y: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
        },
      },
    });

    const monthBudgets = budgets[month] || {};
    const budgetCats = Object.keys(monthBudgets).filter((c) => monthBudgets[c] > 0);
    const budgetLabels = budgetCats.length ? budgetCats : catLabels.slice(0, 6);
    const budgetSpent = budgetLabels.map((c) => byCat[c] || 0);
    const budgetPlanned = budgetLabels.map((c) => Number(monthBudgets[c] || 0));

    destroyChart("budget");
    const budgetCanvas = $("#chart-budget");
    if (budgetCanvas) {
      charts.budget = new Chart(budgetCanvas, {
        type: "bar",
        data: {
          labels: budgetLabels,
          datasets: [
            { label: "Presupuesto", data: budgetPlanned, backgroundColor: "#5c9ead" },
            { label: "Gasto real", data: budgetSpent, backgroundColor: "#3dd6c3" },
          ],
        },
        options: {
          plugins: { legend: { labels: { color: "#8fa3b8" } } },
          scales: {
            x: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
            y: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
          },
        },
      });
    }
  }

  function fillCategorySelects() {
    const opts = categories.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
    $("#rule-category-select").innerHTML = opts;
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  function renderBudgetForm() {
    const grid = $("#budget-grid");
    if (!grid) return;
    const month = currentMonth();
    const monthBudgets = budgets[month] || {};
    grid.innerHTML = categories
      .map(
        (c) => `<label class="budget-row"><span>${escapeHtml(c)}</span>
        <input type="number" min="0" step="1" data-budget-cat="${escapeHtml(c)}" value="${monthBudgets[c] ?? ""}" placeholder="€" /></label>`
      )
      .join("");
  }

  function renderFixedCategories() {
    const box = $("#fixed-categories");
    if (!box) return;
    box.innerHTML = categories
      .map(
        (c) =>
          `<label class="check-inline"><input type="checkbox" data-fixed-cat="${escapeHtml(c)}" ${fixedCategories.includes(c) ? "checked" : ""} /> ${escapeHtml(c)}</label>`
      )
      .join("");
  }

  function collectBudgetsFromForm() {
    const month = currentMonth();
    const monthBudgets = {};
    $("#budget-grid")?.querySelectorAll("[data-budget-cat]").forEach((inp) => {
      const v = parseFloat(inp.value);
      if (Number.isFinite(v) && v > 0) monthBudgets[inp.dataset.budgetCat] = v;
    });
    budgets[month] = monthBudgets;
  }

  function renderMovements() {
    const month = currentMonth();
    const q = ($("#search-movements")?.value || "").toLowerCase();
    const onlyUncl = $("#filter-unclassified")?.checked;
    let list = filterTxs(txsForMonth(month));
    if (q) list = list.filter((t) => t.concept.toLowerCase().includes(q));
    if (onlyUncl) list = list.filter((t) => t.category === "Otros");
    list.sort((a, b) => (a.date < b.date ? 1 : -1));

    const body = $("#movements-body");
    body.innerHTML = list
      .map((t) => {
        const amtClass = t.amount < 0 ? "amount-expense" : "amount-income";
        const catOpts = categories
          .map((c) => `<option value="${escapeHtml(c)}" ${c === t.category ? "selected" : ""}>${escapeHtml(c)}</option>`)
          .join("");
        const tags = (t.tags || []).join(", ");
        return `<tr data-id="${escapeHtml(t.id)}">
          <td>${escapeHtml(t.date)}</td>
          <td>${escapeHtml(t.concept)}</td>
          <td class="${amtClass}">${formatEur(t.amount)}</td>
          <td><select class="cat-edit">${catOpts}</select></td>
          <td><input class="tag-edit" value="${escapeHtml(tags)}" placeholder="etiquetas" /></td>
        </tr>`;
      })
      .join("");

    body.querySelectorAll(".cat-edit").forEach((sel) => {
      sel.addEventListener("change", async (e) => {
        const tr = e.target.closest("tr");
        await patchTx(tr.dataset.id, { category: e.target.value });
      });
    });
    body.querySelectorAll(".tag-edit").forEach((inp) => {
      inp.addEventListener("change", async (e) => {
        const tr = e.target.closest("tr");
        const tags = e.target.value.split(/[,;]/).map((x) => x.trim()).filter(Boolean);
        await patchTx(tr.dataset.id, { tags });
      });
    });
  }

  async function patchTx(id, patch) {
    await api("/api/transactions.php", { method: "PATCH", body: JSON.stringify({ id, ...patch }) });
    await refreshTransactions();
    renderKpis();
    renderCharts();
  }

  function renderRules() {
    const ul = $("#rules-list");
    ul.innerHTML = rules
      .map(
        (r, i) =>
          `<li><span><strong>${escapeHtml(r.pattern)}</strong> → ${escapeHtml(r.category)}${r.tags?.length ? ` · ${escapeHtml(r.tags.join(", "))}` : ""}</span><button type="button" data-i="${i}">Quitar</button></li>`
      )
      .join("");
    ul.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        rules.splice(Number(btn.dataset.i), 1);
        await api("/api/store.php", { method: "PUT", body: JSON.stringify({ rules }) });
        renderRules();
      });
    });
  }

  function exportMonthCsv() {
    const month = currentMonth();
    let list = filterTxs(txsForMonth(month));
    const header = ["fecha", "concepto", "importe", "categoria", "etiquetas", "tipo", "cuenta"];
    const lines = [header.join(";")];
    list.forEach((t) => {
      lines.push(
        [t.date, t.concept, t.amount, t.category || "", (t.tags || []).join(","), t.type || "", t.account || ""]
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(";")
      );
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `hogar-finanzas-${month}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function renderAll() {
    renderKpis();
    renderCharts();
    renderMovements();
    renderBudgetForm();
  }

  function setupTabs() {
    $$(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        $$(".tab").forEach((t) => {
          t.classList.toggle("is-active", t === tab);
          t.setAttribute("aria-selected", t === tab ? "true" : "false");
        });
        const name = tab.dataset.tab;
        $$("[data-panel]").forEach((p) => {
          p.hidden = p.dataset.panel !== name;
        });
      });
    });
  }

  function renderMapUI(headers) {
    const map = buildMapOptions(headers);
    const fields = [
      ["date", "Fecha"],
      ["concept", "Concepto"],
      ["amount", "Importe (una columna)"],
      ["debit", "Cargo / debe (opcional)"],
      ["credit", "Abono / haber (opcional)"],
      ["category", "Categoría (opcional)"],
      ["account", "Cuenta (opcional)"],
    ];
    $("#map-grid").innerHTML = fields
      .map(([key, label]) => {
        const opts = headers.map((h) => `<option value="${escapeHtml(h)}" ${h === map[key] ? "selected" : ""}>${escapeHtml(h)}</option>`).join("");
        return `<label><span>${label}</span><select data-map="${key}"><option value="">—</option>${opts}</select></label>`;
      })
      .join("");
    $("#map-section").hidden = false;
  }

  function readMapFromUI() {
    const map = {};
    $("#map-grid").querySelectorAll("[data-map]").forEach((sel) => {
      map[sel.dataset.map] = sel.value;
    });
    localStorage.setItem(MAP_KEY, JSON.stringify(map));
    return map;
  }

  async function parseFileToRows(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith(".csv")) {
      const text = await file.text();
      const delim = text.includes(";") ? ";" : ",";
      const lines = text.trim().split(/\r?\n/).filter(Boolean);
      if (lines.length < 2) return { headers: [], rows: [] };
      const headers = lines[0].split(delim).map((h) => h.trim().replace(/^"|"$/g, ""));
      const rows = lines.slice(1).map((line) => {
        const cols = line.split(delim).map((c) => c.trim().replace(/^"|"$/g, ""));
        const row = {};
        headers.forEach((h, i) => {
          row[h] = cols[i] ?? "";
        });
        return row;
      });
      return { headers, rows };
    }
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array", cellDates: true });
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });
    const headers = rows.length ? Object.keys(rows[0]) : [];
    return { headers, rows };
  }

  async function mergeFiles(files) {
    parsedRows = [];
    parsedHeaders = [];
    for (const file of files) {
      const { headers, rows } = await parseFileToRows(file);
      if (!parsedHeaders.length) parsedHeaders = headers;
      parsedRows.push(...rows);
    }
    if (parsedHeaders.length) renderMapUI(parsedHeaders);
    $("#import-result").textContent = `${parsedRows.length} filas listas (${files.length} fichero(s)).`;
  }

  async function handleFile(file) {
    const { headers, rows } = await parseFileToRows(file);
    parsedHeaders = headers;
    parsedRows = rows;
    renderMapUI(parsedHeaders);
    $("#import-result").textContent = `${parsedRows.length} filas listas para importar.`;
  }

  async function importParsed() {
    const map = readMapFromUI();
    const hasAmount = map.amount || map.debit || map.credit;
    if (!map.date || !map.concept || !hasAmount) {
      $("#import-result").textContent = "Selecciona fecha, concepto e importe (o columnas cargo/abono).";
      return;
    }
    const rows = rowsToTransactions(parsedRows, map);
    const res = await api("/api/import.php", { method: "POST", body: JSON.stringify({ rows }) });
    $("#import-result").textContent = `Importados: ${res.added}. Duplicados omitidos: ${res.skipped}. Total en base: ${res.total}.`;
    await refreshTransactions();
    renderAll();
  }

  function setupImport() {
    const dz = $("#dropzone");
    const input = $("#file-input");
    $("#pick-file").addEventListener("click", () => input.click());
    input.addEventListener("change", () => {
      const files = [...(input.files || [])];
      if (files.length === 1) handleFile(files[0]);
      else if (files.length > 1) mergeFiles(files);
    });
    dz.addEventListener("dragover", (e) => {
      e.preventDefault();
      dz.classList.add("is-dragover");
    });
    dz.addEventListener("dragleave", () => dz.classList.remove("is-dragover"));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      dz.classList.remove("is-dragover");
      const files = [...(e.dataTransfer.files || [])];
      if (files.length === 1) handleFile(files[0]);
      else if (files.length > 1) mergeFiles(files);
    });
    $("#import-file-btn").addEventListener("click", () => importParsed().catch((e) => {
      $("#import-result").textContent = e.message || "Error al importar";
    }));

    $("#fetch-sheet-btn").addEventListener("click", async () => {
      const url = $("#sheet-url").value.trim();
      if (!url) return;
      const res = await api("/api/sheet.php", { method: "POST", body: JSON.stringify({ url }) });
      parsedRows = res.rows;
      parsedHeaders = res.headers;
      renderMapUI(parsedHeaders);
      $("#import-result").textContent = `${parsedRows.length} filas desde Google Sheet.`;
    });
  }

  function setupGate() {
    $("#gate-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const t = $("#gate-token").value.trim();
      setToken(t);
      try {
        await loadStore();
        await refreshTransactions();
        showApp();
        renderAll();
      } catch (err) {
        clearToken();
        showGate(err.status === 401 ? "Clave incorrecta." : "No se pudo entrar.");
      }
    });
    $("#logout-btn").addEventListener("click", () => {
      clearToken();
      showGate();
    });
  }

  $("#rule-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const pattern = String(fd.get("pattern") || "").trim();
    const category = String(fd.get("category") || "Otros");
    const tags = String(fd.get("tags") || "")
      .split(/[,;]/)
      .map((x) => x.trim())
      .filter(Boolean);
    rules.push({ pattern, category, tags });
    await api("/api/store.php", { method: "PUT", body: JSON.stringify({ rules }) });
    e.target.reset();
    renderRules();
  });

  $("#month-select")?.addEventListener("change", () => {
    syncYearFromMonth();
    renderAll();
  });
  $("#year-select")?.addEventListener("change", () => {
    const y = $("#year-select").value;
    const m = currentMonth().slice(5, 7);
    $("#month-select").value = `${y}-${m}`;
    renderAll();
  });
  $("#search-movements")?.addEventListener("input", renderMovements);
  $("#filter-unclassified")?.addEventListener("change", renderMovements);
  $("#filter-tag")?.addEventListener("input", () => {
    renderKpis();
    renderCharts();
  });
  $("#filter-tag-movements")?.addEventListener("input", renderMovements);
  $("#export-csv-btn")?.addEventListener("click", exportMonthCsv);

  $("#reapply-rules-btn")?.addEventListener("click", async () => {
    const res = await api("/api/reapply-rules.php", {
      method: "POST",
      body: JSON.stringify({ month: currentMonth() }),
    });
    await refreshTransactions();
    renderAll();
    alert(`Reclasificados: ${res.updated} movimientos.`);
  });
  $("#reapply-rules-all-btn")?.addEventListener("click", async () => {
    const res = await api("/api/reapply-rules.php", { method: "POST", body: JSON.stringify({}) });
    await refreshTransactions();
    renderAll();
    alert(`Reclasificados: ${res.updated} movimientos.`);
  });

  $("#save-budgets-btn")?.addEventListener("click", async () => {
    collectBudgetsFromForm();
    await api("/api/store.php", { method: "PUT", body: JSON.stringify({ budgets }) });
    renderCharts();
  });

  $("#save-fixed-btn")?.addEventListener("click", async () => {
    fixedCategories = [];
    $("#fixed-categories")?.querySelectorAll("[data-fixed-cat]:checked").forEach((cb) => {
      fixedCategories.push(cb.dataset.fixedCat);
    });
    await api("/api/store.php", { method: "PUT", body: JSON.stringify({ fixed_categories: fixedCategories }) });
    renderKpis();
  });

  setupTabs();
  setupGate();
  setupImport();
  setDefaultMonth();
  bootstrap();
})();
