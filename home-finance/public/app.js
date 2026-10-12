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
      date: ["fecha", "date", "f. valor", "valor"],
      concept: ["concepto", "descripcion", "descripción", "detail", "merchant", "beneficiario"],
      amount: ["importe", "amount", "cantidad", "cargo", "abono"],
      category: ["categoria", "categoría", "category"],
      account: ["cuenta", "account", "tarjeta"],
    };
    const saved = JSON.parse(localStorage.getItem(MAP_KEY) || "{}");
    return {
      date: saved.date || guessHeader(headers, { date: patterns.date }),
      concept: saved.concept || guessHeader(headers, { concept: patterns.concept }),
      amount: saved.amount || guessHeader(headers, { amount: patterns.amount }),
      category: saved.category || guessHeader(headers, { category: patterns.category }),
      account: saved.account || guessHeader(headers, { account: patterns.account }),
    };
  }

  function rowsToTransactions(rows, map) {
    return rows
      .map((row) => {
        const date = parseDate(row[map.date]);
        const concept = String(row[map.concept] ?? "").trim();
        let amount = parseAmount(row[map.amount]);
        const category = map.category ? String(row[map.category] ?? "").trim() : "";
        const account = map.account ? String(row[map.account] ?? "").trim() : "";
        if (!date || !concept) return null;
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
    $("#gate").hidden = false;
    $("#app").hidden = true;
    const err = $("#gate-error");
    if (msg) {
      err.textContent = msg;
      err.hidden = false;
    } else {
      err.hidden = true;
    }
  }

  function showApp() {
    $("#gate").hidden = true;
    $("#app").hidden = false;
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
    fillCategorySelects();
    renderRules();
  }

  async function refreshTransactions() {
    const data = await api("/api/transactions.php");
    allTransactions = data.transactions || [];
  }

  function txsForMonth(month) {
    return allTransactions.filter((t) => t.month === month);
  }

  function prevMonth(month) {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m - 2, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function sumExpenses(txs) {
    return txs.filter((t) => t.type !== "ingreso" && t.amount < 0).reduce((s, t) => s + Math.abs(t.amount), 0);
  }

  function sumIncome(txs) {
    return txs.filter((t) => t.type === "ingreso" || t.amount > 0).reduce((s, t) => s + Math.abs(t.amount), 0);
  }

  function renderKpis() {
    const month = currentMonth();
    const cur = txsForMonth(month);
    const prev = txsForMonth(prevMonth(month));
    const expenses = sumExpenses(cur);
    const income = sumIncome(cur);
    const prevExp = sumExpenses(prev);
    const delta = prevExp > 0 ? ((expenses - prevExp) / prevExp) * 100 : 0;
    const unclassified = cur.filter((t) => t.category === "Otros" && t.amount < 0).length;
    const days = new Date(month + "-01");
    const dim = new Date(days.getFullYear(), days.getMonth() + 1, 0).getDate();
    const daily = expenses / dim;

    $("#kpi-grid").innerHTML = `
      <div class="kpi"><div class="kpi-label">Gastos del mes</div><div class="kpi-value negative">${formatEur(expenses)}</div></div>
      <div class="kpi"><div class="kpi-label">Ingresos</div><div class="kpi-value positive">${formatEur(income)}</div></div>
      <div class="kpi"><div class="kpi-label">Balance</div><div class="kpi-value ${income - expenses >= 0 ? "positive" : "negative"}">${formatEur(income - expenses)}</div></div>
      <div class="kpi"><div class="kpi-label">vs mes anterior</div><div class="kpi-value">${delta >= 0 ? "+" : ""}${delta.toFixed(1)}%</div><div class="kpi-sub">en gastos</div></div>
      <div class="kpi"><div class="kpi-label">Media / día</div><div class="kpi-value">${formatEur(daily)}</div></div>
      <div class="kpi"><div class="kpi-label">Sin clasificar</div><div class="kpi-value">${unclassified}</div><div class="kpi-sub">categoría Otros</div></div>
    `;
  }

  function destroyChart(id) {
    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }
  }

  function renderCharts() {
    const month = currentMonth();
    const cur = txsForMonth(month).filter((t) => t.amount < 0 && t.type !== "ingreso");

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
    for (let i = 5; i >= 0; i--) {
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
          x: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
          y: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
        },
      },
    });
  }

  function fillCategorySelects() {
    const opts = categories.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
    $("#rule-category-select").innerHTML = opts;
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  function renderMovements() {
    const month = currentMonth();
    const q = ($("#search-movements")?.value || "").toLowerCase();
    const onlyUncl = $("#filter-unclassified")?.checked;
    let list = txsForMonth(month);
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

  function renderAll() {
    renderKpis();
    renderCharts();
    renderMovements();
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
      ["amount", "Importe"],
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

  async function handleFile(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith(".csv")) {
      const text = await file.text();
      const delim = text.includes(";") ? ";" : ",";
      const lines = text.trim().split(/\r?\n/);
      parsedHeaders = lines[0].split(delim).map((h) => h.trim().replace(/^"|"$/g, ""));
      parsedRows = lines.slice(1).map((line) => {
        const cols = line.split(delim).map((c) => c.trim().replace(/^"|"$/g, ""));
        const row = {};
        parsedHeaders.forEach((h, i) => {
          row[h] = cols[i] ?? "";
        });
        return row;
      });
    } else {
      const buf = await file.arrayBuffer();
      const wb = XLSX.read(buf, { type: "array", cellDates: true });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });
      parsedRows = json;
      parsedHeaders = json.length ? Object.keys(json[0]) : [];
    }
    renderMapUI(parsedHeaders);
    $("#import-result").textContent = `${parsedRows.length} filas listas para importar.`;
  }

  async function importParsed() {
    const map = readMapFromUI();
    if (!map.date || !map.concept || !map.amount) {
      $("#import-result").textContent = "Selecciona al menos fecha, concepto e importe.";
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
      if (input.files[0]) handleFile(input.files[0]);
    });
    dz.addEventListener("dragover", (e) => {
      e.preventDefault();
      dz.classList.add("is-dragover");
    });
    dz.addEventListener("dragleave", () => dz.classList.remove("is-dragover"));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      dz.classList.remove("is-dragover");
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
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

  $("#month-select")?.addEventListener("change", renderAll);
  $("#search-movements")?.addEventListener("input", renderMovements);
  $("#filter-unclassified")?.addEventListener("change", renderMovements);

  setupTabs();
  setupGate();
  setupImport();
  setDefaultMonth();
  bootstrap();
})();
