const API = "/api/salesnav-admin-api.php";

let activeTab = "overview";
let usersCache = [];

function $(id) {
  return document.getElementById(id);
}

function setFlash(text, tone = "ok") {
  const el = $("admin-flash");
  if (!el) return;
  if (!text) {
    el.hidden = true;
    el.textContent = "";
    el.className = "admin-flash";
    return;
  }
  el.hidden = false;
  el.textContent = text;
  el.className = `admin-flash is-${tone === "err" ? "err" : "ok"}`;
}

async function api(action, opts = {}) {
  const url = new URL(API, window.location.origin);
  url.searchParams.set("action", action);
  if (opts.query) {
    Object.entries(opts.query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString(), {
    method: opts.method || "GET",
    credentials: "same-origin",
    headers: opts.body ? { "Content-Type": "application/json" } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    data = {};
  }
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso.slice(0, 16);
  }
}

function fmtNum(n) {
  return Number(n || 0).toLocaleString();
}

function showApp(authenticated) {
  $("admin-login").hidden = authenticated;
  $("admin-app").hidden = !authenticated;
}

async function checkStatus() {
  try {
    const data = await api("status");
    if (!data.admin_configured) {
      setLoginNote("Admin not configured on server (SALESNAV_ADMIN_SECRET).", "err");
      return false;
    }
    showApp(!!data.authenticated);
    if (data.authenticated) {
      await loadActiveTab();
    }
    return !!data.authenticated;
  } catch (err) {
    setLoginNote(err.message, "err");
    showApp(false);
    return false;
  }
}

function setLoginNote(text, tone = "err") {
  const el = $("admin-login-note");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
  el.className = `account-note admin-login-note${tone === "err" ? " error" : ""}`;
}

async function login(token) {
  await api("login", { method: "POST", body: { token } });
  showApp(true);
  setLoginNote("");
  await loadActiveTab();
}

async function logout() {
  try {
    await api("logout", { method: "POST", body: {} });
  } catch {
    /* ignore */
  }
  showApp(false);
  $("admin-token").value = "";
}

function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll(".admin-tab").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".admin-panel").forEach((panel) => {
    const on = panel.dataset.panel === tab;
    panel.hidden = !on;
    panel.classList.toggle("is-active", on);
  });
  loadActiveTab();
}

async function loadActiveTab() {
  if (activeTab === "overview") await loadOverview();
  if (activeTab === "users") await loadUsers();
  if (activeTab === "ledger") await loadLedger();
  if (activeTab === "tasks") await loadTasks();
}

async function loadOverview() {
  const data = await api("overview");
  const o = data.overview || {};
  const stats = [
    ["Users", fmtNum(o.users_total)],
    ["Verified", fmtNum(o.users_verified)],
    ["Credits in wallets", fmtNum(o.credits_in_circulation)],
    ["Tasks (total)", fmtNum(o.tasks_total)],
    ["Ready", fmtNum(o.tasks_by_status?.ready)],
    ["Failed", fmtNum(o.tasks_by_status?.failed)],
    ["Top-ups (30d)", fmtNum(o.credits_topup_30d)],
    ["Grants (30d)", fmtNum(o.credits_granted_30d)],
    ["Spent (30d)", fmtNum(o.credits_spent_30d)],
  ];
  $("admin-stats").innerHTML = stats
    .map(
      ([label, value]) =>
        `<article class="admin-stat"><p class="admin-stat-label">${label}</p><p class="admin-stat-value">${value}</p></article>`
    )
    .join("");
}

function renderUsers(users) {
  const tbody = $("users-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="8">No users found.</td></tr>';
    return;
  }
  users.forEach((u) => {
    const tr = document.createElement("tr");
    tr.className = "is-clickable";
    tr.dataset.userId = u.user_id;
    const liClass = u.linkedin_invalid ? "warn" : u.linkedin_connected ? "ok" : "";
    const liText = u.linkedin_invalid ? "Expired" : u.linkedin_connected ? "OK" : "—";
    tr.innerHTML = `
      <td>${u.email || '<span class="mono">' + (u.user_id || "").slice(0, 14) + "…</span>"}</td>
      <td>${fmtNum(u.balance)}</td>
      <td>${fmtNum(u.credits_purchased)}</td>
      <td>${fmtNum(u.credits_granted)}</td>
      <td>${fmtNum(u.credits_spent)}</td>
      <td>${fmtNum(u.task_count)} <span class="muted">(${fmtNum(u.tasks_ready)} ok)</span></td>
      <td>${liClass ? `<span class="admin-badge ${liClass}">${liText}</span>` : "—"}</td>
      <td>${u.email_verified ? '<span class="admin-badge ok">Yes</span>' : "—"}</td>`;
    tr.addEventListener("click", () => openUserDrawer(u.user_id));
    tbody.appendChild(tr);
  });
}

async function loadUsers() {
  const q = ($("users-search")?.value || "").trim();
  const data = await api("users", { query: q ? { q } : {} });
  usersCache = data.users || [];
  renderUsers(usersCache);
}

async function loadLedger() {
  const kind = $("ledger-kind")?.value || "all";
  const data = await api("ledger", { query: { limit: 200, kind } });
  const tbody = $("ledger-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  (data.ledger || []).forEach((row) => {
    const tr = document.createElement("tr");
    const delta = Number(row.delta || 0);
    tr.innerHTML = `
      <td>${fmtDate(row.ts)}</td>
      <td>${row.email || "—"}</td>
      <td>${row.kind || "—"}</td>
      <td>${delta > 0 ? "+" : ""}${fmtNum(delta)}</td>
      <td>${fmtNum(row.balance)}</td>
      <td class="mono">${(row.ref || "").slice(0, 28)}${(row.ref || "").length > 28 ? "…" : ""}</td>`;
    tbody.appendChild(tr);
  });
}

async function loadTasks() {
  const status = $("tasks-status-filter")?.value || "all";
  const data = await api("tasks", { query: { limit: 150, status } });
  const tbody = $("tasks-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  (data.tasks || []).forEach((t) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${fmtDate(t.created_at)}</td>
      <td>${t.email || "—"}</td>
      <td>${t.source_label || t.mode || "—"}</td>
      <td><span class="task-status" data-status="${t.status}">${t.status}</span></td>
      <td>${t.status === "ready" ? fmtNum(t.lead_count) : "—"}</td>
      <td>${t.status === "ready" ? fmtNum(t.credits_used) : "—"}</td>
      <td class="mono">${t.id || "—"}</td>`;
    tbody.appendChild(tr);
  });
}

async function openUserDrawer(userId) {
  const data = await api("user", { query: { user_id: userId } });
  const d = data.detail || {};
  const u = d.user || {};
  $("drawer-title").textContent = u.email || userId;
  const li = d.linkedin || {};
  $("drawer-body").innerHTML = `
    <dl class="admin-detail-grid">
      <dt>Email</dt><dd>${u.email || "—"}</dd>
      <dt>User id</dt><dd class="mono">${u.user_id || "—"}</dd>
      <dt>Balance</dt><dd>${fmtNum(u.balance)} credits</dd>
      <dt>Purchased (Stripe)</dt><dd>${fmtNum(u.credits_purchased)}</dd>
      <dt>Granted (admin)</dt><dd>${fmtNum(u.credits_granted)}</dd>
      <dt>Spent</dt><dd>${fmtNum(u.credits_spent)}</dd>
      <dt>Verified</dt><dd>${u.email_verified ? "Yes" : "No"}</dd>
      <dt>LinkedIn</dt><dd>${li.account_id ? (li.invalid_at ? "Expired" : "Connected") + " · " + (li.label || li.account_id) : "Not linked"}</dd>
    </dl>
    <h3>Recent ledger</h3>
    ${renderSubtable(
      ["When", "Δ", "Kind", "Ref"],
      (d.ledger || []).slice(0, 15).map((r) => [
        fmtDate(r.ts),
        (r.delta > 0 ? "+" : "") + fmtNum(r.delta),
        r.kind,
        (r.ref || "").slice(0, 20),
      ])
    )}
    <h3>Recent tasks</h3>
    ${renderSubtable(
      ["Created", "Status", "Leads", "Source"],
      (d.tasks || []).slice(0, 10).map((t) => [
        fmtDate(t.created_at),
        t.status,
        t.status === "ready" ? fmtNum(t.lead_count) : "—",
        t.source_label || "—",
      ])
    )}
    <div class="account-actions" style="margin-top:1rem">
      <button type="button" class="connect-btn" id="drawer-grant-btn">Grant credits to this user</button>
    </div>`;
  $("admin-drawer").hidden = false;
  $("drawer-grant-btn")?.addEventListener("click", () => {
    switchTab("grant");
    $("grant-email").value = u.email || "";
    $("admin-drawer").hidden = true;
  });
}

function renderSubtable(headers, rows) {
  if (!rows.length) return "<p class=\"muted\">None</p>";
  const head = headers.map((h) => `<th>${h}</th>`).join("");
  const body = rows.map((cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
  return `<table class="admin-subtable"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bindEvents() {
  $("admin-login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = $("admin-token")?.value || "";
    setLoginNote("");
    try {
      await login(token.trim());
    } catch (err) {
      setLoginNote(err.message, "err");
    }
  });

  $("admin-logout-btn")?.addEventListener("click", () => logout());

  document.querySelectorAll(".admin-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab || "overview"));
  });

  $("users-search")?.addEventListener("input", () => {
    clearTimeout(window._usersSearchTimer);
    window._usersSearchTimer = setTimeout(() => loadUsers(), 250);
  });
  $("users-refresh")?.addEventListener("click", () => loadUsers());
  $("ledger-kind")?.addEventListener("change", () => loadLedger());
  $("ledger-refresh")?.addEventListener("click", () => loadLedger());
  $("tasks-status-filter")?.addEventListener("change", () => loadTasks());
  $("tasks-refresh")?.addEventListener("click", () => loadTasks());

  $("drawer-close")?.addEventListener("click", () => {
    $("admin-drawer").hidden = true;
  });

  $("grant-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = ($("grant-email")?.value || "").trim();
    const credits = Number($("grant-credits")?.value || 0);
    const note = ($("grant-note")?.value || "").trim();
    try {
      const result = await api("grant", { method: "POST", body: { email, credits, note } });
      setFlash(`Granted ${fmtNum(result.granted)} credits to ${result.email}. New balance: ${fmtNum(result.balance)}.`);
      $("grant-result").hidden = false;
      $("grant-result").textContent = JSON.stringify(result, null, 2);
      if (activeTab === "users") await loadUsers();
      if (activeTab === "overview") await loadOverview();
    } catch (err) {
      setFlash(err.message, "err");
    }
  });
}

bindEvents();
checkStatus();
