const API = "/api/salesnav-admin-api.php";

const PAGE_META = {
  overview: { title: "Overview", sub: "Platform metrics at a glance" },
  users: { title: "Users", sub: "Accounts, balances and activity" },
  ledger: { title: "Ledger", sub: "Credit movements — top-ups, grants, spend" },
  tasks: { title: "Tasks", sub: "Export jobs across all users" },
  grant: { title: "Grant credits", sub: "Assign free credits to a user" },
};

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
    el.className = "sn-flash";
    return;
  }
  el.hidden = false;
  el.textContent = text;
  el.className = `sn-flash is-${tone === "err" ? "err" : "ok"}`;
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

function kindBadge(kind) {
  const k = (kind || "other").toLowerCase();
  return `<span class="sn-badge kind-${k}">${k}</span>`;
}

function statusBadge(status) {
  const s = (status || "").toLowerCase();
  return `<span class="sn-badge status-${s}">${status}</span>`;
}

function showApp(authenticated) {
  $("admin-login").hidden = authenticated;
  $("admin-app").hidden = !authenticated;
  document.body.classList.toggle("is-authed", authenticated);
}

function setPageMeta(tab) {
  const meta = PAGE_META[tab] || PAGE_META.overview;
  const titleEl = $("page-title");
  const subEl = $("page-sub");
  if (titleEl) titleEl.textContent = meta.title;
  if (subEl) subEl.textContent = meta.sub;
}

async function checkStatus() {
  try {
    const data = await api("status");
    if (!data.admin_configured) {
      setLoginNote("Admin not configured on server (SALESNAV_ADMIN_SECRET).");
      return false;
    }
    showApp(!!data.authenticated);
    if (data.authenticated) {
      await loadActiveTab();
    }
    return !!data.authenticated;
  } catch (err) {
    setLoginNote(err.message);
    showApp(false);
    return false;
  }
}

function setLoginNote(text) {
  const el = $("admin-login-note");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
}

async function login(token) {
  await api("login", { method: "POST", body: { token } });
  showApp(true);
  setLoginNote("");
  setPageMeta(activeTab);
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
  setPageMeta(tab);
  document.querySelectorAll(".sn-nav-item").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".sn-panel").forEach((panel) => {
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
    { label: "Total users", value: fmtNum(o.users_total) },
    { label: "Verified", value: fmtNum(o.users_verified), cls: "success" },
    { label: "Credits in wallets", value: fmtNum(o.credits_in_circulation), cls: "accent" },
    { label: "Tasks total", value: fmtNum(o.tasks_total) },
    { label: "Ready", value: fmtNum(o.tasks_by_status?.ready), cls: "success" },
    { label: "Failed", value: fmtNum(o.tasks_by_status?.failed), cls: "warning" },
    { label: "Top-ups (30d)", value: fmtNum(o.credits_topup_30d), cls: "accent" },
    { label: "Grants (30d)", value: fmtNum(o.credits_granted_30d) },
    { label: "Spent (30d)", value: fmtNum(o.credits_spent_30d) },
  ];
  $("admin-stats").innerHTML = stats
    .map(
      (s) =>
        `<article class="sn-stat${s.cls ? " " + s.cls : ""}"><p class="sn-stat-label">${s.label}</p><p class="sn-stat-value">${s.value}</p></article>`
    )
    .join("");
}

function renderUsers(users) {
  const tbody = $("users-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  if (!users.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No users found.</td></tr>';
    return;
  }
  users.forEach((u) => {
    const tr = document.createElement("tr");
    tr.className = "is-clickable";
    tr.dataset.userId = u.user_id;
    const liClass = u.linkedin_invalid ? "warn" : u.linkedin_connected ? "ok" : "neutral";
    const liText = u.linkedin_invalid ? "Expired" : u.linkedin_connected ? "Connected" : "—";
    tr.innerHTML = `
      <td><strong>${u.email || '<span class="mono">' + (u.user_id || "").slice(0, 16) + "…</span>"}</strong></td>
      <td><strong>${fmtNum(u.balance)}</strong></td>
      <td>${fmtNum(u.credits_purchased)}</td>
      <td>${fmtNum(u.credits_granted)}</td>
      <td>${fmtNum(u.credits_spent)}</td>
      <td>${fmtNum(u.task_count)} <span class="muted">${fmtNum(u.tasks_ready)} ok</span></td>
      <td>${u.linkedin_connected || u.linkedin_invalid ? `<span class="sn-badge ${liClass}">${liText}</span>` : "—"}</td>
      <td>${u.email_verified ? '<span class="sn-badge ok">Verified</span>' : '<span class="sn-badge neutral">—</span>'}</td>`;
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
  const rows = data.ledger || [];
  if (!rows.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="6">No ledger entries.</td></tr>';
    return;
  }
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const delta = Number(row.delta || 0);
    const deltaCls = delta > 0 ? "sn-delta-pos" : delta < 0 ? "sn-delta-neg" : "";
    tr.innerHTML = `
      <td>${fmtDate(row.ts)}</td>
      <td>${row.email || "—"}</td>
      <td>${kindBadge(row.kind)}</td>
      <td class="${deltaCls}">${delta > 0 ? "+" : ""}${fmtNum(delta)}</td>
      <td>${fmtNum(row.balance)}</td>
      <td class="mono" title="${row.ref || ""}">${(row.ref || "").slice(0, 32)}${(row.ref || "").length > 32 ? "…" : ""}</td>`;
    tbody.appendChild(tr);
  });
}

async function loadTasks() {
  const status = $("tasks-status-filter")?.value || "all";
  const data = await api("tasks", { query: { limit: 150, status } });
  const tbody = $("tasks-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  const rows = data.tasks || [];
  if (!rows.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No tasks found.</td></tr>';
    return;
  }
  rows.forEach((t) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${fmtDate(t.created_at)}</td>
      <td>${t.email || "—"}</td>
      <td>${t.source_label || t.mode || "—"}</td>
      <td>${statusBadge(t.status)}</td>
      <td>${t.status === "ready" ? fmtNum(t.lead_count) : "—"}</td>
      <td>${t.status === "ready" ? fmtNum(t.credits_used) : "—"}</td>
      <td class="mono">${t.id || "—"}</td>`;
    tbody.appendChild(tr);
  });
}

function closeDrawer() {
  $("admin-drawer").hidden = true;
  $("drawer-backdrop").hidden = true;
}

async function openUserDrawer(userId) {
  const data = await api("user", { query: { user_id: userId } });
  const d = data.detail || {};
  const u = d.user || {};
  $("drawer-title").textContent = u.email || userId;
  const li = d.linkedin || {};
  $("drawer-body").innerHTML = `
    <dl class="sn-detail-grid">
      <div class="sn-detail-item"><dt>Balance</dt><dd>${fmtNum(u.balance)} credits</dd></div>
      <div class="sn-detail-item"><dt>Verified</dt><dd>${u.email_verified ? "Yes" : "No"}</dd></div>
      <div class="sn-detail-item"><dt>Purchased</dt><dd>${fmtNum(u.credits_purchased)}</dd></div>
      <div class="sn-detail-item"><dt>Granted</dt><dd>${fmtNum(u.credits_granted)}</dd></div>
      <div class="sn-detail-item"><dt>Spent</dt><dd>${fmtNum(u.credits_spent)}</dd></div>
      <div class="sn-detail-item"><dt>Tasks</dt><dd>${fmtNum(u.task_count)}</dd></div>
      <div class="sn-detail-item" style="grid-column:1/-1"><dt>User ID</dt><dd class="mono">${u.user_id || "—"}</dd></div>
      <div class="sn-detail-item" style="grid-column:1/-1"><dt>LinkedIn</dt><dd>${li.account_id ? (li.invalid_at ? "Expired" : "Connected") + " · " + (li.label || li.account_id) : "Not linked"}</dd></div>
    </dl>
    <div class="sn-drawer-section">
      <h3>Recent ledger</h3>
      ${renderSubtable(
        ["When", "Δ", "Kind", "Ref"],
        (d.ledger || []).slice(0, 12).map((r) => [
          fmtDate(r.ts),
          (r.delta > 0 ? "+" : "") + fmtNum(r.delta),
          r.kind,
          (r.ref || "").slice(0, 18),
        ])
      )}
    </div>
    <div class="sn-drawer-section">
      <h3>Recent tasks</h3>
      ${renderSubtable(
        ["Created", "Status", "Leads", "Source"],
        (d.tasks || []).slice(0, 8).map((t) => [
          fmtDate(t.created_at),
          t.status,
          t.status === "ready" ? fmtNum(t.lead_count) : "—",
          t.source_label || "—",
        ])
      )}
    </div>
    <div class="sn-drawer-actions">
      <button type="button" class="sn-btn sn-btn-primary sn-btn-block" id="drawer-grant-btn">Grant credits</button>
    </div>`;
  $("admin-drawer").hidden = false;
  $("drawer-backdrop").hidden = false;
  $("drawer-grant-btn")?.addEventListener("click", () => {
    closeDrawer();
    switchTab("grant");
    $("grant-email").value = u.email || "";
  });
}

function renderSubtable(headers, rows) {
  if (!rows.length) return '<p class="muted" style="color:var(--sn-text-faint);font-size:0.85rem">None</p>';
  const head = headers.map((h) => `<th>${h}</th>`).join("");
  const body = rows.map((cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
  return `<table class="sn-subtable"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bindEvents() {
  $("admin-login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = $("admin-token")?.value || "";
    setLoginNote("");
    try {
      await login(token.trim());
    } catch (err) {
      setLoginNote(err.message);
    }
  });

  $("admin-logout-btn")?.addEventListener("click", () => logout());

  document.querySelectorAll(".sn-nav-item").forEach((btn) => {
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

  $("drawer-close")?.addEventListener("click", closeDrawer);
  $("drawer-backdrop")?.addEventListener("click", closeDrawer);

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

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });
}

bindEvents();
checkStatus();
