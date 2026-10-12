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
  let pivotImport = false;
  let pivotMeta = "";
  let pendingWb = null;
  let pendingFileName = "";

  const SPANISH_MONTHS = {
    enero: 1,
    febrero: 2,
    marzo: 3,
    abril: 4,
    mayo: 5,
    junio: 6,
    julio: 7,
    agosto: 8,
    septiembre: 9,
    setiembre: 9,
    octubre: 10,
    noviembre: 11,
    diciembre: 12,
  };
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
    const m = currentMonth();
    if (el) el.value = m;
    const pf = $("#period-from");
    const pt = $("#period-to");
    if (pf && !pf.value) pf.value = m;
    if (pt && !pt.value) pt.value = m;
    syncYearFromMonth();
    updatePeriodLabel();
  }

  function periodBounds() {
    let from = $("#period-from")?.value || currentMonth();
    let to = $("#period-to")?.value || from;
    if (from > to) {
      const tmp = from;
      from = to;
      to = tmp;
      if ($("#period-from")) $("#period-from").value = from;
      if ($("#period-to")) $("#period-to").value = to;
    }
    return { from, to };
  }

  function monthsInRange(from, to) {
    const months = [];
    const [y1, m1] = from.split("-").map(Number);
    const [y2, m2] = to.split("-").map(Number);
    let y = y1;
    let m = m1;
    while (y < y2 || (y === y2 && m <= m2)) {
      months.push(`${y}-${String(m).padStart(2, "0")}`);
      m += 1;
      if (m > 12) {
        m = 1;
        y += 1;
      }
    }
    return months;
  }

  function txsInPeriod() {
    const { from, to } = periodBounds();
    return filterTxs(
      allTransactions.filter((t) => {
        const mo = t.month || (t.date || "").slice(0, 7);
        return mo >= from && mo <= to;
      })
    );
  }

  function formatPeriodLabel() {
    const { from, to } = periodBounds();
    if (from === to) return `Mes ${from}`;
    return `${from} → ${to} (${monthsInRange(from, to).length} meses)`;
  }

  function updatePeriodLabel() {
    const el = $("#period-label");
    if (el) el.textContent = `Mostrando: ${formatPeriodLabel()}. Los totales y gráficos usan este rango.`;
  }

  function applyPeriodPreset(preset) {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth() + 1;
    const cur = `${y}-${String(m).padStart(2, "0")}`;
    let from = cur;
    let to = cur;
    if (preset === "month") {
      from = to = currentMonth();
    } else if (preset === "last3") {
      const d = new Date(y, m - 1 - 2, 1);
      from = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      to = cur;
    } else if (preset === "last12") {
      const d = new Date(y, m - 1 - 11, 1);
      from = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      to = cur;
    } else if (preset === "ytd") {
      from = `${y}-01`;
      to = cur;
    }
    if ($("#period-from")) $("#period-from").value = from;
    if ($("#period-to")) $("#period-to").value = to;
    if ($("#month-select")) $("#month-select").value = to;
    updatePeriodLabel();
    renderAll();
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

  function monthFromHeader(cell) {
    if (cell === null || cell === undefined) return 0;
    if (typeof cell === "number" && cell >= 1 && cell <= 12) return cell;
    const s = String(cell).trim().toLowerCase().replace(/\./g, "");
    if (SPANISH_MONTHS[s]) return SPANISH_MONTHS[s];
    const ym = s.match(/^(\d{4})-(\d{2})$/);
    if (ym) return parseInt(ym[2], 10);
    return 0;
  }

  function yearFromSheetName(name) {
    const m = String(name).match(/(20\d{2})/);
    return m ? parseInt(m[1], 10) : 0;
  }

  function sheetFlowKind(sheetName) {
    const n = String(sheetName)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
    if (/ingreso|ingresos|salario|nomina|nominas|sueldo|entrada/.test(n)) return "ingreso";
    return "gasto";
  }

  function isSkipConcept(concept) {
    const c = String(concept).trim();
    if (!c) return true;
    if (/^total|suma|subtotal|media/i.test(c)) return true;
    if (/^20\d{2}$/.test(c)) return true;
    return false;
  }

  /** Filas de ingreso dentro de la matriz anual (también aparecen en pestaña ingresos). */
  function isMatrixIncomeConcept(concept) {
    const c = String(concept)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
    if (/^ingresos?\b/.test(c)) return true;
    if (/\b(salario|nomina|nominas|sueldo)\b/.test(c)) return true;
    return false;
  }

  function pushMatrixTx(transactions, { date, concept, abs, sheetName, asIncome }) {
    if (asIncome) {
      transactions.push({
        date,
        concept,
        amount: abs,
        type: "ingreso",
        category: "Ingresos",
        account: sheetName,
        tags: ["casa-matriz", "ingreso"],
      });
    } else {
      transactions.push({
        date,
        concept,
        amount: -abs,
        type: "gasto",
        category: "",
        account: sheetName,
        tags: ["casa-matriz", "gasto"],
      });
    }
  }

  /** Excel tipo "Gastos Casa": filas = conceptos, columnas = meses */
  function parsePivotMatrix(matrix, sheetName) {
    if (!matrix || matrix.length < 2) return null;

    let year = yearFromSheetName(sheetName);
    let headerRow = -1;
    let monthColumns = [];
    let conceptCol = 0;

    for (let r = 0; r < Math.min(8, matrix.length); r++) {
      const row = matrix[r] || [];
      const found = [];
      for (let c = 0; c < row.length; c++) {
        const mn = monthFromHeader(row[c]);
        if (mn) found.push({ col: c, month: mn });
      }
      if (found.length >= 3) {
        headerRow = r;
        monthColumns = found;
        const y0 = row[0];
        if (typeof y0 === "number" && y0 >= 2000 && y0 <= 2100) year = y0;
        conceptCol = found[0].col >= 2 ? 1 : 0;
        break;
      }
    }

    if (headerRow < 0 && matrix[0]) {
      const a0 = matrix[0][0];
      if (typeof a0 === "number" && a0 >= 2000 && a0 <= 2100) {
        year = a0;
        headerRow = 0;
        conceptCol = 0;
        for (let c = 1; c < matrix[0].length; c++) {
          const mn = monthFromHeader(matrix[0][c]);
          if (mn) monthColumns.push({ col: c, month: mn });
        }
      }
    }

    if (!year || monthColumns.length < 3) return null;

    const transactions = [];
    for (let r = headerRow + 1; r < matrix.length; r++) {
      const row = matrix[r] || [];
      let concept = row[conceptCol];
      if (concept === null || concept === undefined) {
        if (conceptCol === 0 && row[1]) concept = row[1];
        else continue;
      }
      concept = String(concept).trim();
      if (isSkipConcept(concept)) continue;

      for (const { col, month } of monthColumns) {
        const raw = row[col];
        if (raw === null || raw === undefined || raw === "") continue;
        const amount = parseAmount(raw);
        if (amount === 0) continue;
        const date = `${year}-${String(month).padStart(2, "0")}-01`;
        const abs = Math.abs(amount);
        const sheetFlow = sheetFlowKind(sheetName);
        const asIncome = sheetFlow === "ingreso" || isMatrixIncomeConcept(concept);
        pushMatrixTx(transactions, { date, concept, abs, sheetName, asIncome });
      }
    }

    if (transactions.length < 3) return null;
    return { transactions, year, sheetName };
  }

  function parseSingleSheet(wb, sheetName) {
    const sheet = wb.Sheets[sheetName];
    if (!sheet) return null;
    const matrix = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: null });
    const pivot = parsePivotMatrix(matrix, sheetName);
    if (pivot?.transactions?.length >= 3) {
      return {
        isPivot: true,
        rows: pivot.transactions,
        pivotParts: [`${sheetName} (año ${pivot.year}, ${pivot.transactions.length} mov.)`],
      };
    }
    const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });
    const headers = rows.length ? Object.keys(rows[0]) : [];
    return { isPivot: false, rows, headers };
  }

  function hideImportPanels() {
    $("#map-section").hidden = true;
    $("#pivot-section").hidden = true;
    $("#sheet-picker-section").hidden = true;
  }

  function showSheetPicker(sheetNames, fileName) {
    hideImportPanels();
    const sec = $("#sheet-picker-section");
    const sel = $("#sheet-select");
    if (!sec || !sel) return;
    sec.hidden = false;
    sel.innerHTML = sheetNames.map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`).join("");
    const prefer =
      sheetNames.find((n) => /^20\d{2}$/.test(String(n).trim())) ||
      sheetNames.find((n) => /2026/.test(n)) ||
      sheetNames[sheetNames.length - 1];
    if (prefer) sel.value = prefer;
    $("#import-result").textContent = `«${fileName}»: elige una de las ${sheetNames.length} pestañas.`;
  }

  function applyWorkbookSheet(wb, sheetName, fileName) {
    const parsed = parseSingleSheet(wb, sheetName);
    if (!parsed) {
      $("#import-result").textContent = "No se pudo leer la pestaña seleccionada.";
      return;
    }
    parsedRows = parsed.rows;
    parsedHeaders = parsed.headers || [];
    const fileLabel = fileName ? `«${fileName}» · ` : "";
    if (parsed.isPivot) {
      showPivotImport(
        `${fileLabel}pestaña «${sheetName}». Matriz conceptos × meses. ${
          sheetFlowKind(sheetName) === "ingreso"
            ? "Detectada como INGRESOS (importes positivos)."
            : "Detectada como GASTOS (importes negativos)."
        } ${parsed.pivotParts?.join(" ") || ""}`,
        parsedRows
      );
    } else {
      showColumnImport(parsedHeaders);
    }
    $("#import-result").textContent = `${parsedRows.length} filas listas — solo pestaña «${sheetName}».`;
  }

  function applyAllWorkbookSheets(wb, fileName) {
    const parts = [];
    const allRows = [];
    let ingresoCount = 0;
    let gastoCount = 0;
    for (const sheetName of wb.SheetNames) {
      const parsed = parseSingleSheet(wb, sheetName);
      if (!parsed?.isPivot || !parsed.rows?.length) continue;
      allRows.push(...parsed.rows);
      if (sheetFlowKind(sheetName) === "ingreso") ingresoCount += parsed.rows.length;
      else gastoCount += parsed.rows.length;
      parts.push(`«${sheetName}» (${parsed.rows.length})`);
    }
    if (allRows.length < 3) {
      $("#import-result").textContent =
        "No hay hojas matriz válidas. Usa «Cargar esta pestaña» o revisa el formato del Excel.";
      return;
    }
    const fileLabel = fileName ? `«${fileName}» · ` : "";
    showPivotImport(
      `${fileLabel}Todas las pestañas matriz: ${allRows.length} movimientos (${ingresoCount} líneas ingreso, ${gastoCount} gasto). ${parts.join(" · ")}`,
      allRows
    );
    $("#import-result").textContent = `${allRows.length} filas listas — ingresos + gastos de ${parts.length} pestaña(s).`;
  }

  async function loadExcelFile(file) {
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array", cellDates: true });
    pendingWb = wb;
    pendingFileName = file.name;
    if (wb.SheetNames.length > 1) {
      showSheetPicker(wb.SheetNames, file.name);
      return;
    }
    applyWorkbookSheet(wb, wb.SheetNames[0], file.name);
  }

  function showPivotImport(summary, rows) {
    pivotImport = true;
    parsedRows = rows;
    parsedHeaders = [];
    hideImportPanels();
    const ps = $("#pivot-section");
    if (ps) ps.hidden = false;
    const el = $("#pivot-summary");
    if (el) el.textContent = summary;
  }

  function showColumnImport(headers) {
    pivotImport = false;
    hideImportPanels();
    renderMapUI(headers);
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
      try {
        const dedupe = await api("/api/dedupe-mirrors.php", { method: "POST" });
        if (dedupe.removed > 0) {
          await refreshTransactions();
        }
      } catch {
        /* optional cleanup */
      }
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
    renderCategoriesList();
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
    return allTransactions.filter((t) => (t.month || (t.date || "").slice(0, 7)) === month);
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
    const { from, to } = periodBounds();
    const cur = txsInPeriod();
    const monthCount = monthsInRange(from, to).length;
    const expenses = sumExpenses(cur);
    const income = sumIncome(cur);
    const flow = income - expenses;
    const unclassified = cur.filter((t) => t.category === "Otros" && t.amount < 0).length;
    const { fixed, variable } = sumFixedVariable(cur);
    const avgMonthExp = monthCount > 0 ? expenses / monthCount : 0;

    let prevDelta = "";
    if (from === to) {
      const prev = filterTxs(txsForMonth(prevMonth(from)));
      const prevExp = sumExpenses(prev);
      const delta = prevExp > 0 ? ((expenses - prevExp) / prevExp) * 100 : 0;
      prevDelta = `<div class="kpi"><div class="kpi-label">vs mes anterior</div><div class="kpi-value">${delta >= 0 ? "+" : ""}${delta.toFixed(1)}%</div><div class="kpi-sub">en gastos</div></div>`;
    }

    $("#kpi-grid").innerHTML = `
      <div class="kpi"><div class="kpi-label">Ingresos (periodo)</div><div class="kpi-value positive">${formatEur(income)}</div></div>
      <div class="kpi"><div class="kpi-label">Gastos (periodo)</div><div class="kpi-value negative">${formatEur(expenses)}</div></div>
      <div class="kpi"><div class="kpi-label">Flujo / tesorería</div><div class="kpi-value ${flow >= 0 ? "positive" : "negative"}">${formatEur(flow)}</div><div class="kpi-sub">ingresos − gastos</div></div>
      <div class="kpi"><div class="kpi-label">Media gasto / mes</div><div class="kpi-value">${formatEur(avgMonthExp)}</div><div class="kpi-sub">${monthCount} mes(es)</div></div>
      <div class="kpi"><div class="kpi-label">Gastos fijos</div><div class="kpi-value">${formatEur(fixed)}</div><div class="kpi-sub">variable ${formatEur(variable)}</div></div>
      ${prevDelta}
      <div class="kpi"><div class="kpi-label">Sin clasificar</div><div class="kpi-value">${unclassified}</div><div class="kpi-sub">categoría Otros</div></div>
    `;
    updatePeriodLabel();
    renderReminder();
  }

  function destroyChart(id) {
    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }
  }

  function renderCharts() {
    const { from, to } = periodBounds();
    const cur = txsInPeriod().filter(isExpenseTx);

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

    const months = monthsInRange(from, to);
    const trend = months.map((mo) => sumExpenses(txsForMonth(mo)));
    const trendIncome = months.map((mo) => sumIncome(txsForMonth(mo)));

    destroyChart("trend");
    charts.trend = new Chart($("#chart-trend"), {
      type: "line",
      data: {
        labels: months,
        datasets: [
          { label: "Gastos", data: trend, borderColor: "#f07178", tension: 0.3, fill: false },
          { label: "Ingresos", data: trendIncome, borderColor: "#7fd99a", tension: 0.3, fill: false },
        ],
      },
      options: {
        plugins: { legend: { labels: { color: "#8fa3b8" } } },
        scales: {
          x: { ticks: { color: "#8fa3b8", maxRotation: 45 }, grid: { color: "#2f3d4f" } },
          y: { ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
        },
      },
    });

    destroyChart("cashflow");
    const cfCanvas = $("#chart-cashflow");
    if (cfCanvas && months.length) {
      const flow = months.map((mo, i) => trendIncome[i] - trend[i]);
      charts.cashflow = new Chart(cfCanvas, {
        type: "bar",
        data: {
          labels: months,
          datasets: [
            { label: "Ingresos", data: trendIncome, backgroundColor: "#7fd99a" },
            { label: "Gastos", data: trend.map((v) => -v), backgroundColor: "#f07178" },
            { label: "Flujo neto", data: flow, type: "line", borderColor: "#3dd6c3", backgroundColor: "transparent", yAxisID: "y" },
          ],
        },
        options: {
          plugins: { legend: { labels: { color: "#8fa3b8" } } },
          scales: {
            x: { stacked: true, ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
            y: { stacked: true, ticks: { color: "#8fa3b8" }, grid: { color: "#2f3d4f" } },
          },
        },
      });
    }

  }

  function categoriesSorted(extra) {
    const set = new Set(categories);
    if (extra) set.add(extra);
    return [...set].sort((a, b) => a.localeCompare(b, "es"));
  }

  function fillCategorySelects() {
    const opts = categoriesSorted()
      .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
      .join("");
    const sel = $("#rule-category-select");
    if (sel) sel.innerHTML = opts;
  }

  function renderCategoriesList() {
    const ul = $("#categories-list");
    if (!ul) return;
    ul.innerHTML = categoriesSorted()
      .map(
        (c) =>
          `<li><span>${escapeHtml(c)}</span><button type="button" data-cat="${escapeHtml(c)}" title="Quitar de la lista">×</button></li>`
      )
      .join("");
    ul.querySelectorAll("button[data-cat]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const name = btn.dataset.cat;
        const inUse = allTransactions.some((t) => t.category === name);
        if (inUse && !confirm(`«${name}» sigue en movimientos. ¿Quitarla solo del desplegable?`)) return;
        categories = categories.filter((c) => c !== name);
        await api("/api/store.php", { method: "PUT", body: JSON.stringify({ categories }) });
        fillCategorySelects();
        renderCategoriesList();
        renderBudgetForm();
        renderFixedCategories();
        renderMovements();
      });
    });
  }

  async function addCategory(name) {
    const n = String(name || "").trim();
    if (!n) return;
    if (categories.some((c) => c.toLowerCase() === n.toLowerCase())) {
      alert(`La categoría «${n}» ya existe.`);
      return;
    }
    categories.push(n);
    categories = categoriesSorted();
    try {
      await api("/api/store.php", { method: "PUT", body: JSON.stringify({ categories }) });
      await loadStore();
      const inp = $("#category-name-input");
      if (inp) inp.value = "";
    } catch (err) {
      categories = categories.filter((c) => c !== n);
      alert(err.message === "unauthorized" ? "Sesión caducada. Vuelve a entrar." : "No se pudo guardar la categoría.");
      throw err;
    }
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
    const q = ($("#search-movements")?.value || "").toLowerCase();
    const onlyUncl = $("#filter-unclassified")?.checked;
    let list = txsInPeriod();
    if (q) list = list.filter((t) => t.concept.toLowerCase().includes(q));
    if (onlyUncl) list = list.filter((t) => t.category === "Otros");
    list.sort((a, b) => (a.date < b.date ? 1 : -1));

    const body = $("#movements-body");
    body.innerHTML = list
      .map((t) => {
        const amtClass = t.amount < 0 ? "amount-expense" : "amount-income";
        const catOpts = categoriesSorted(t.category)
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
        await patchTx(tr.dataset.id, { category: e.target.value }, { remember: true });
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

  async function patchTx(id, patch, opts = {}) {
    await api("/api/transactions.php", { method: "PATCH", body: JSON.stringify({ id, ...patch }) });
    if (patch.category) {
      await loadStore();
    }
    await refreshTransactions();
    renderKpis();
    renderCharts();
    renderMovements();
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
    const { from, to } = periodBounds();
    let list = txsInPeriod();
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
    a.download = `hogar-finanzas-${from}_${to}.csv`;
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
      return { headers, rows, isPivot: false };
    }
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array", cellDates: true });
    if (wb.SheetNames.length > 1) {
      return { needsSheetPick: true };
    }
    const parsed = parseSingleSheet(wb, wb.SheetNames[0]);
    return parsed || { headers: [], rows: [], isPivot: false };
  }

  async function excelHasMultipleSheets(file) {
    if (!/\.xlsx?$/i.test(file.name)) return false;
    const wb = XLSX.read(await file.arrayBuffer(), { type: "array", cellDates: true });
    return wb.SheetNames.length > 1;
  }

  async function mergeFiles(files) {
    for (const file of files) {
      if (await excelHasMultipleSheets(file)) {
        $("#import-result").textContent =
          "Si el Excel tiene varias pestañas, súbelo solo (un fichero) para elegir la hoja.";
        await loadExcelFile(file);
        return;
      }
    }
    parsedRows = [];
    parsedHeaders = [];
    let anyPivot = false;
    const parts = [];
    for (const file of files) {
      const parsed = await parseFileToRows(file);
      if (parsed.isPivot) {
        anyPivot = true;
        parts.push(...(parsed.pivotParts || []));
        parsedRows.push(...parsed.rows);
      } else {
        if (!parsedHeaders.length) parsedHeaders = parsed.headers;
        parsedRows.push(...parsed.rows);
      }
    }
    if (anyPivot && parsedRows.length >= 3) {
      showPivotImport(
        `Varias hojas/ficheros en formato matriz. Total: ${parsedRows.length} movimientos. ${parts.join(" · ")}`,
        parsedRows
      );
    } else if (parsedHeaders.length) showColumnImport(parsedHeaders);
    $("#import-result").textContent = `${parsedRows.length} filas listas (${files.length} fichero(s)).`;
  }

  async function handleFile(file) {
    pendingWb = null;
    hideImportPanels();
    if (/\.xlsx?$/i.test(file.name)) {
      await loadExcelFile(file);
      return;
    }
    const parsed = await parseFileToRows(file);
    parsedHeaders = parsed.headers || [];
    parsedRows = parsed.rows || [];
    if (parsed.isPivot) {
      showPivotImport(
        `Formato matriz en «${file.name}». ${parsed.pivotParts?.join(" · ") || ""} Total: ${parsedRows.length} movimientos.`,
        parsedRows
      );
    } else {
      showColumnImport(parsedHeaders);
    }
    $("#import-result").textContent = `${parsedRows.length} filas listas para importar.`;
  }

  async function importParsed() {
    let rows;
    if (pivotImport) {
      rows = parsedRows;
    } else {
      const map = readMapFromUI();
      const hasAmount = map.amount || map.debit || map.credit;
      if (!map.date || !map.concept || !hasAmount) {
        $("#import-result").textContent = "Selecciona fecha, concepto e importe (o columnas cargo/abono).";
        return;
      }
      rows = rowsToTransactions(parsedRows, map);
    }
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
    const runImport = () =>
      importParsed().catch((e) => {
        $("#import-result").textContent = e.message || "Error al importar";
      });
    $("#import-file-btn").addEventListener("click", runImport);
    $("#import-pivot-btn")?.addEventListener("click", runImport);
    $("#sheet-apply-btn")?.addEventListener("click", () => {
      if (!pendingWb) return;
      const sheetName = $("#sheet-select")?.value;
      if (!sheetName) return;
      applyWorkbookSheet(pendingWb, sheetName, pendingFileName);
    });
    $("#sheet-all-btn")?.addEventListener("click", () => {
      if (!pendingWb) return;
      applyAllWorkbookSheets(pendingWb, pendingFileName);
    });

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

  $("#category-add-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await addCategory(fd.get("name"));
    } catch {
      /* addCategory ya avisa */
    }
  });

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
    const m = currentMonth();
    if ($("#period-from")) $("#period-from").value = m;
    if ($("#period-to")) $("#period-to").value = m;
    syncYearFromMonth();
    renderAll();
  });
  $("#period-from")?.addEventListener("change", renderAll);
  $("#period-to")?.addEventListener("change", renderAll);
  $$("[data-preset]").forEach((btn) => {
    btn.addEventListener("click", () => applyPeriodPreset(btn.dataset.preset));
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
