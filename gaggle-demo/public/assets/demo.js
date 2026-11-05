const API = '/api';
const MEMBER_PLATFORM_STORAGE = 'ngaged_platform_id';
const DASH_DAYS_STORAGE = 'ngaged_dash_days';
let currentAdmin = null;

function getAdminKey() {
  return localStorage.getItem('ngaged_admin_key') || '';
}

function readStoredDashDays() {
  const raw = localStorage.getItem(DASH_DAYS_STORAGE);
  if (raw === 'all') return 'all';
  const n = parseInt(raw || '7', 10);
  return n === 30 ? 30 : 7;
}

let dashDays = readStoredDashDays();
let chartInstances = {};

function $(sel, root = document) {
  return root.querySelector(sel);
}

function setStatus(el, message, kind = '') {
  if (!el) return;
  el.textContent = message || '';
  const base = el.classList.contains('alert') ? 'alert py-2' : 'status';
  el.className = base + (kind === 'ok' ? ' alert-success' : kind === 'err' ? ' alert-danger' : kind ? ' alert-info' : '');
  el.hidden = !message;
}

const PAGE_META = {
  dashboard: ['Dashboard', 'Métricas de adopción y amplificación'],
  campaigns: ['Crear campaña', 'Publica advocacy por email one-click'],
  'campaigns-history': ['Historial', 'Campañas enviadas y resultados'],
  members: ['Miembros', 'Directorio del equipo'],
  'members-invite': ['Invitar LinkedIn', 'Invita a tu equipo a conectar su perfil'],
  connections: ['Cuentas LinkedIn', 'Canales conectados al workspace'],
  employee: ['Vista empleado', 'Cola de reposts pendientes'],
  settings: ['Ajustes', 'Accesos admin y estado del sistema'],
};

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.admin) {
    const legacy = getAdminKey();
    if (legacy) headers['X-Demo-Admin-Key'] = legacy;
  }
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }
  const res = await fetch(API + path, { ...options, headers, credentials: 'include' });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && data.loginRequired && !path.includes('admin-me')) {
    window.location.href = '/login';
    throw new Error('Sesión expirada');
  }
  if (!res.ok) {
    throw new Error(data.error || res.statusText || 'Request failed');
  }
  return data;
}

async function ensureAdminSession() {
  const data = await api('/admin-me');
  if (data.auth !== 'session') {
    localStorage.removeItem('ngaged_admin_key');
    localStorage.removeItem('gaggle_demo_admin_key');
    window.location.href = '/login';
    return null;
  }
  currentAdmin = data.admin || null;
  const label = $('#admin-user-label');
  if (label && currentAdmin?.email) {
    label.textContent = currentAdmin.name ? currentAdmin.name + ' · ' + currentAdmin.email : currentAdmin.email;
    label.classList.remove('d-none');
  }
  const emailEl = $('#settings-admin-email');
  if (emailEl && currentAdmin?.email) emailEl.textContent = currentAdmin.email;
  return currentAdmin;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return iso;
  }
}

function navigateTo(id) {
  const links = document.querySelectorAll('.sidebar-link[data-panel]');
  // Only content sections — sidebar buttons also carry data-panel and must stay visible.
  const panels = document.querySelectorAll('.admin-content section[data-panel]');
  links.forEach((l) => l.classList.toggle('active', l.getAttribute('data-panel') === id));
  panels.forEach((p) => {
    p.hidden = p.getAttribute('data-panel') !== id;
  });
  const meta = PAGE_META[id] || ['Ngaged', ''];
  const title = $('#page-title');
  const sub = $('#page-subtitle');
  if (title) title.textContent = meta[0];
  if (sub) sub.textContent = meta[1];
  if (id === 'dashboard') {
    loadDashboard();
    scheduleChartResize();
  }
  if (id === 'campaigns') refreshCampaignMemberPicks();
  if (id === 'campaigns-history') refreshCampaignsList();
  if (id === 'members' || id === 'members-invite') refreshMembers();
  if (id === 'connections') refreshConnectionsTable();
  if (id === 'employee') refreshMemberQueue();
  if (id === 'settings') {
    renderHealthChecks();
    refreshAdminUsers();
  }
  if (isMobileNav()) setSidebarOpen(false);
}

function isMobileNav() {
  return window.matchMedia('(max-width: 991.98px)').matches;
}

function setSidebarOpen(open) {
  const sidebar = $('#admin-sidebar');
  const overlay = $('#sidebar-overlay');
  const toggle = $('#sidebar-toggle');
  if (!sidebar) return;
  sidebar.classList.toggle('is-open', open);
  if (overlay) {
    overlay.classList.toggle('is-visible', open);
    overlay.hidden = !open;
    overlay.setAttribute('aria-hidden', open ? 'false' : 'true');
  }
  document.body.classList.toggle('sidebar-nav-open', open);
  if (toggle) {
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Cerrar menú de navegación' : 'Abrir menú de navegación');
  }
  if (!open) {
    scheduleChartResize();
  }
}

function resizeCharts() {
  Object.values(chartInstances).forEach((ch) => {
    try {
      ch?.resize?.();
    } catch {
      /* ignore */
    }
  });
}

function scheduleChartResize() {
  requestAnimationFrame(() => {
    requestAnimationFrame(resizeCharts);
  });
}

function initMobileNav() {
  const toggle = $('#sidebar-toggle');
  const overlay = $('#sidebar-overlay');
  toggle?.addEventListener('click', () => {
    const sidebar = $('#admin-sidebar');
    setSidebarOpen(!sidebar?.classList.contains('is-open'));
  });
  overlay?.addEventListener('click', () => setSidebarOpen(false));
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setSidebarOpen(false);
  });
  window.addEventListener('resize', () => {
    if (!isMobileNav()) setSidebarOpen(false);
    scheduleChartResize();
  });
  window.addEventListener('orientationchange', scheduleChartResize);
}

function initNav() {
  document.querySelectorAll('.sidebar-link[data-panel]').forEach((link) => {
    link.addEventListener('click', () => navigateTo(link.getAttribute('data-panel')));
  });
  document.querySelectorAll('[data-goto]').forEach((btn) => {
    btn.addEventListener('click', () => navigateTo(btn.getAttribute('data-goto')));
  });
}

function initAdminAuthUi() {
  $('#admin-logout-btn')?.addEventListener('click', async () => {
    try {
      await api('/admin-logout', { method: 'POST' });
    } catch {
      /* ignore */
    }
    window.location.href = '/login';
  });
}

async function refreshAdminUsers() {
  const list = $('#admin-users-list');
  const form = $('#admin-invite-form');
  const statusEl = $('#admin-users-status');
  if (!list) return;
  if (currentAdmin?.role !== 'owner') {
    form.hidden = true;
    list.innerHTML = '<li class="list-group-item text-muted">Solo el administrador principal gestiona accesos.</li>';
    return;
  }
  form.hidden = false;
  try {
    const data = await api('/admins', { admin: true });
    const rows = data.admins || [];
    list.innerHTML = rows
      .map(
        (a) =>
          '<li class="list-group-item d-flex justify-content-between align-items-center gap-2">' +
          '<span>' +
          escapeHtml(a.name || a.email) +
          '<br/><span class="text-muted">' +
          escapeHtml(a.email) +
          '</span></span>' +
          '<span class="badge ' +
          (a.active ? 'text-bg-success' : 'text-bg-secondary') +
          '">' +
          escapeHtml(a.role) +
          '</span></li>'
      )
      .join('');
  } catch (e) {
    setStatus(statusEl, e.message, 'err');
  }
}

function initAdminUsersPanel() {
  $('#create-admin-btn')?.addEventListener('click', async () => {
    const statusEl = $('#admin-users-status');
    const name = $('#new-admin-name')?.value.trim() || '';
    const email = $('#new-admin-email')?.value.trim() || '';
    const password = $('#new-admin-password')?.value || '';
    setStatus(statusEl, 'Creando acceso…');
    try {
      await api('/admins', { method: 'POST', admin: true, body: { name, email, password, role: 'admin' } });
      setStatus(statusEl, 'Acceso creado. Comparte el email y la contraseña inicial.', 'ok');
      $('#new-admin-name').value = '';
      $('#new-admin-email').value = '';
      $('#new-admin-password').value = '';
      await refreshAdminUsers();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
}

async function loadConnections() {
  const data = await api('/connections');
  return data.connections || [];
}

function destroyCharts() {
  Object.values(chartInstances).forEach((c) => c.destroy());
  chartInstances = {};
}

function renderKpis(totals) {
  const grid = $('#kpi-grid');
  const cards = [
    { label: 'Campañas enviadas', value: totals.campaigns, sub: totals.campaignsThisMonth ? '+' + totals.campaignsThisMonth + ' este mes' : '' },
    { label: 'Invitaciones enviadas', value: totals.invitesSent },
    { label: 'Amplificaciones', value: totals.reposted, hero: false },
    { label: 'Tasa de adopción', value: (totals.adoptionRate ?? 0) + '%', hero: true },
    { label: 'Pendientes', value: totals.pending },
    { label: 'Sin acción', value: totals.declined },
  ];
  if (totals.medianHoursToRepost != null) {
    cards.push({ label: 'Tiempo medio hasta repost', value: totals.medianHoursToRepost + ' h' });
  }
  grid.innerHTML = cards
    .map((c) => {
      const col = c.hero ? 'col-md-6 col-xl-4' : 'col-6 col-md-4 col-xl-2';
      return (
        '<div class="' +
        col +
        '"><div class="card shadow-sm h-100' +
        (c.hero ? ' border-primary' : '') +
        '"><div class="card-body"><div class="text-muted small">' +
        escapeHtml(c.label) +
        '</div><div class="fs-3 fw-bold">' +
        escapeHtml(String(c.value)) +
        '</div>' +
        (c.sub ? '<div class="text-success small">' + escapeHtml(c.sub) + '</div>' : '') +
        '</div></div></div>'
      );
    })
    .join('');
}

function chartColors() {
  return {
    brand: '#0a66c2',
    ok: '#1b7f4b',
    muted: '#94a3b8',
    warn: '#d97706',
  };
}

function renderCharts(data) {
  if (typeof Chart === 'undefined') return;
  destroyCharts();
  const c = chartColors();
  const mix = data.series.responseMix;

  chartInstances.donut = new Chart($('#chart-donut'), {
    type: 'doughnut',
    data: {
      labels: ['Reposteado', 'Ignorado', 'Pendiente'],
      datasets: [
        {
          data: [mix.reposted, mix.declined, mix.pending],
          backgroundColor: [c.ok, c.muted, c.warn],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 400 },
      plugins: { legend: { position: 'bottom' } },
    },
  });

  const daily = data.series.daily || [];
  chartInstances.line = new Chart($('#chart-line'), {
    type: 'line',
    data: {
      labels: daily.map((d) => d.date),
      datasets: [
        { label: 'Campañas', data: daily.map((d) => d.campaigns), borderColor: c.brand, tension: 0.35 },
        { label: 'Reposts', data: daily.map((d) => d.reposts), borderColor: c.ok, tension: 0.35 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 400 },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });

  const sent = data.totals.invitesSent || 0;
  chartInstances.funnel = new Chart($('#chart-funnel'), {
    type: 'bar',
    data: {
      labels: ['Enviados', 'Reposteados', 'Ignorados', 'Pendientes'],
      datasets: [
        {
          data: [sent, mix.reposted, mix.declined, mix.pending],
          backgroundColor: [c.brand, c.ok, c.muted, c.warn],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: 'y',
      animation: { duration: 400 },
      plugins: { legend: { display: false } },
    },
  });

  const top = data.topMembers || [];
  chartInstances.top = new Chart($('#chart-top'), {
    type: 'bar',
    data: {
      labels: top.map((m) => m.name),
      datasets: [{ label: 'Reposts', data: top.map((m) => m.reposts), backgroundColor: c.brand }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: 'y',
      animation: { duration: 400 },
      plugins: { legend: { display: false } },
    },
  });
  scheduleChartResize();
}

function renderRecentTable(rows, options) {
  const demo = options && options.demo;
  const tbody = $('#recent-campaigns-table tbody');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Sin campañas en este periodo.</td></tr>';
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r) =>
        '<tr><td>' +
        escapeHtml(r.title) +
        '</td><td>' +
        escapeHtml(formatDate(r.createdAt)) +
        '</td><td>' +
        r.sent +
        '</td><td>' +
        r.reposted +
        '</td><td>' +
        r.rate +
        '%</td><td>' +
        (demo
          ? '<span class="text-muted small">Demo</span>'
          : '<button type="button" class="btn btn-secondary btn-sm" data-detail="' +
            escapeHtml(r.id) +
            '">Detalle</button>') +
        '</td></tr>'
    )
    .join('');
  if (!demo) {
    tbody.querySelectorAll('[data-detail]').forEach((btn) => {
      btn.addEventListener('click', () => openCampaignDetail(btn.getAttribute('data-detail')));
    });
  }
}

/** Métricas simuladas para el dashboard vacío (se ocultan con actividad real). */
function buildDashboardDemoStats(daysParam) {
  const spanDays = daysParam === 'all' ? 30 : Math.max(7, parseInt(String(daysParam), 10) || 30);
  const daily = [];
  const now = new Date();
  let sumCamp = 0;
  let sumRepost = 0;
  for (let i = spanDays - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setUTCDate(d.getUTCDate() - i);
    const key = d.toISOString().slice(0, 10);
    const campaigns = i % 5 === 0 ? 1 : 0;
    const reposts = campaigns ? 2 + (i % 3) : i % 7 === 0 ? 1 : 0;
    sumCamp += campaigns;
    sumRepost += reposts;
    daily.push({ date: key, campaigns, reposts });
  }
  const invitesSent = Math.max(42, sumRepost * 2 + 12);
  const reposted = Math.max(28, sumRepost);
  const declined = 7;
  const pending = Math.max(4, invitesSent - reposted - declined);
  const answered = reposted + declined;
  const iso = (offsetDays) => {
    const d = new Date(now);
    d.setUTCDate(d.getUTCDate() - offsetDays);
    return d.toISOString();
  };
  return {
    totals: {
      campaigns: Math.max(5, sumCamp),
      invitesSent,
      reposted,
      declined,
      pending,
      adoptionRate: answered > 0 ? Math.round((100 * reposted) / answered * 10) / 10 : 0,
      medianHoursToRepost: 5.5,
      campaignsThisMonth: 3,
    },
    series: {
      daily,
      responseMix: { reposted, declined, pending },
    },
    topMembers: [
      { memberId: 'demo_1', name: 'Ana García', reposts: 9, adoptionRate: 90 },
      { memberId: 'demo_2', name: 'Carlos Ruiz', reposts: 7, adoptionRate: 88 },
      { memberId: 'demo_3', name: 'Laura Méndez', reposts: 6, adoptionRate: 85 },
      { memberId: 'demo_4', name: 'Miguel Soto', reposts: 5, adoptionRate: 83 },
      { memberId: 'demo_5', name: 'Elena Vidal', reposts: 4, adoptionRate: 80 },
    ],
    recentCampaigns: [
      { id: 'demo_c1', title: 'Lanzamiento producto Q4', sent: 12, reposted: 9, rate: 75, createdAt: iso(2) },
      { id: 'demo_c2', title: 'Caso de éxito cliente', sent: 10, reposted: 8, rate: 80, createdAt: iso(6) },
      { id: 'demo_c3', title: 'Webinar employee advocacy', sent: 11, reposted: 7, rate: 63.6, createdAt: iso(11) },
      { id: 'demo_c4', title: 'Employer branding', sent: 9, reposted: 5, rate: 55.6, createdAt: iso(18) },
      { id: 'demo_c5', title: 'Nota de prensa', sent: 8, reposted: 4, rate: 50, createdAt: iso(24) },
    ],
  };
}

function dashboardHasRealActivity(apiData) {
  const t = apiData.totals || {};
  return (t.invitesSent ?? 0) > 0 || (t.campaigns ?? 0) > 0;
}

async function loadDashboard() {
  const empty = $('#dash-empty');
  const content = $('#dash-content');
  const demoBanner = $('#dash-demo-banner');
  try {
    const q = dashDays === 'all' || dashDays === 0 ? 'all' : String(dashDays);
    const apiData = await api('/stats?days=' + encodeURIComponent(q), { admin: true });
    const hasReal = dashboardHasRealActivity(apiData);
    const data = hasReal ? apiData : buildDashboardDemoStats(q);
    empty.hidden = true;
    content.hidden = false;
    if (demoBanner) demoBanner.hidden = hasReal;
    renderKpis(data.totals);
    renderCharts(data);
    renderRecentTable(data.recentCampaigns || [], { demo: !hasReal });
  } catch (e) {
    empty.hidden = false;
    content.hidden = true;
    if (demoBanner) demoBanner.hidden = true;
    const msgEl = empty.querySelector('p');
    if (msgEl) {
      if (e.message.includes('Sesión') || e.message.includes('sesión') || e.message.includes('Inicia')) {
        msgEl.textContent = 'Inicia sesión en /login para ver los datos del servidor.';
      } else {
        msgEl.textContent = e.message;
      }
    }
  }
}

function initDashboardControls() {
  document.querySelectorAll('button.pill[data-days]').forEach((pill) => {
    const days = pill.getAttribute('data-days');
    pill.classList.toggle(
      'active',
      days === 'all' ? dashDays === 'all' : String(dashDays) === days
    );
    pill.addEventListener('click', () => {
      document.querySelectorAll('button.pill[data-days]').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      const d = pill.getAttribute('data-days');
      dashDays = d === 'all' ? 'all' : parseInt(d, 10);
      localStorage.setItem(DASH_DAYS_STORAGE, String(dashDays));
      loadDashboard();
    });
  });
  $('#dash-refresh').addEventListener('click', loadDashboard);
}

async function refreshConnectionsTable() {
  const tbody = $('#connections-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="4" class="text-muted">Cargando…</td></tr>';
  try {
    const data = await api('/connections');
    const rows = data.connections || [];
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No hay cuentas LinkedIn.</td></tr>';
      return;
    }
    tbody.innerHTML = rows
      .map(
        (c) =>
          '<tr><td>' +
          escapeHtml(c.displayName || c.username || '—') +
          '</td><td><code class="small">' +
          escapeHtml(c.platformId) +
          '</code></td><td>' +
          escapeHtml(c.connectionStatus || '—') +
          '</td><td><button type="button" class="btn btn-link btn-sm copy-pid" data-pid="' +
          escapeHtml(c.platformId) +
          '">Copiar ID</button></td></tr>'
      )
      .join('');
    tbody.querySelectorAll('.copy-pid').forEach((btn) => {
      btn.addEventListener('click', () => {
        navigator.clipboard.writeText(btn.getAttribute('data-pid'));
      });
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-danger">' + escapeHtml(e.message) + '</td></tr>';
  }
}

async function loadWorkspaceBadge() {
  const badge = $('#workspace-badge');
  if (!badge) return;
  try {
    const h = await api('/health');
    badge.textContent = h.linkedinOAuth ? 'OAuth LinkedIn' : 'Vinculación asistida';
    badge.className = 'badge rounded-pill ' + (h.linkedinOAuth ? 'text-bg-success' : 'text-bg-secondary');
    badge.title = h.linkedinOAuth
      ? 'Los empleados pueden autorizar LinkedIn desde su invitación.'
      : 'El admin vincula cuentas en Miembros hasta activar OAuth.';
  } catch {
    badge.textContent = 'Estado API';
  }
}

async function renderHealthChecks() {
  const list = $('#health-checks');
  if (!list) return;
  list.innerHTML = '<li class="list-group-item text-muted">Comprobando…</li>';
  try {
    const h = await api('/health');
    const checks = h.checks || [];
    list.innerHTML = checks
      .map(
        (c) =>
          '<li class="list-group-item d-flex justify-content-between align-items-center">' +
          '<span>' +
          escapeHtml(c.label) +
          '</span>' +
          '<span class="badge rounded-pill ' +
          (c.ok ? 'text-bg-success' : 'text-bg-warning') +
          '">' +
          (c.ok ? 'OK' : 'Revisar') +
          '</span></li>'
      )
      .join('');
    await loadWorkspaceBadge();
  } catch (e) {
    list.innerHTML = '<li class="list-group-item text-danger">' + escapeHtml(e.message) + '</li>';
  }
}

function initSettingsPanel() {
  $('#health-refresh')?.addEventListener('click', renderHealthChecks);
  $('#dedupe-members-btn')?.addEventListener('click', async () => {
    const statusEl = $('#settings-maint-status');
    setStatus(statusEl, 'Fusionando duplicados…');
    try {
      const data = await api('/maintenance-dedupe', { method: 'POST', admin: true, body: {} });
      setStatus(statusEl, 'Listo: ' + data.removed + ' duplicados eliminados.', 'ok');
      await refreshMembers();
      await refreshCampaignMemberPicks();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
}

async function openCampaignDetail(id) {
  const modal = $('#campaign-modal');
  const body = $('#modal-body');
  $('#modal-title').textContent = 'Detalle de campaña';
  body.innerHTML = '<p class="meta">Cargando…</p>';
  modal.showModal();
  try {
    const data = await api('/campaign-detail?id=' + encodeURIComponent(id), { admin: true });
    const rows = data.deliveries || [];
    body.innerHTML =
      '<div class="table-wrap"><table class="data-table"><thead><tr><th>Miembro</th><th>Estado</th><th>Respondió</th></tr></thead><tbody>' +
      rows
        .map((d) => {
          let state = 'Pendiente';
          if (d.action === 'approve') state = 'Reposteado';
          if (d.action === 'decline') state = 'Ignorado';
          if (d.error) state = 'Error';
          return (
            '<tr><td>' +
            escapeHtml(d.name) +
            '</td><td>' +
            escapeHtml(state) +
            '</td><td>' +
            escapeHtml(formatDate(d.respondedAt)) +
            '</td></tr>'
          );
        })
        .join('') +
      '</tbody></table></div>';
  } catch (e) {
    body.innerHTML = '<p class="status err">' + escapeHtml(e.message) + '</p>';
  }
}

let previewState = { preview: {}, urn: '' };
let pendingDispatchCampaignId = null;
let pendingDispatchResend = false;

function memberPickLabel(m, teamNames = {}) {
  const base = (m.name || m.email || 'Miembro').trim();
  const team = m.teamId && teamNames[m.teamId] ? ' · ' + teamNames[m.teamId] : '';
  const li = m.platformId ? '' : ' · sin LinkedIn';
  return base + team + li;
}

function teamNameMap(teams) {
  const map = {};
  (teams || []).forEach((t) => {
    if (t && t.id) map[t.id] = t.name || t.id;
  });
  return map;
}

async function loadMembersBundle() {
  const data = await api('/members', { admin: true });
  return { members: data.members || [], teams: data.teams || [] };
}

/** Multiselect con búsqueda: seleccionados en chips horizontales; opciones en desplegable. */
function mountMemberMultiSelect(container, members, options = {}) {
  container._memberMultiSelect = null;
  if (!members.length) {
    container.className = 'member-multiselect member-multiselect-empty';
    container.innerHTML = '<p class="empty mb-0">Añade miembros en la pestaña Miembros (invitación o manual).</p>';
    return;
  }

  const selected = new Set();
  if (options.selectedIds != null) {
    options.selectedIds.forEach((id) => selected.add(id));
  } else if (options.checkedByDefault) {
    members.forEach((m) => selected.add(m.id));
  }

  const teams = options.teams || [];
  const teamNames = teamNameMap(teams);

  function membersOfTeam(teamId) {
    return members.filter((m) => (m.teamId || '') === teamId);
  }

  container.className = 'member-multiselect';
  container.innerHTML =
    '<div class="member-ms-team-bar flex-wrap align-items-center gap-2 mb-1" hidden></div>' +
    '<div class="member-ms-chips" role="list" aria-label="Destinatarios seleccionados"></div>' +
    '<div class="member-ms-field position-relative">' +
    '<input type="text" class="form-control member-ms-search" placeholder="Escribe para buscar y añadir…" autocomplete="off" aria-expanded="false" aria-controls="' +
    escapeHtml('ms-drop-' + Math.random().toString(36).slice(2, 9)) +
    '" />' +
    '<div class="member-ms-dropdown list-group" hidden role="listbox"></div>' +
    '</div>';

  const teamBarEl = container.querySelector('.member-ms-team-bar');
  const chipsEl = container.querySelector('.member-ms-chips');
  const searchEl = container.querySelector('.member-ms-search');
  const dropEl = container.querySelector('.member-ms-dropdown');
  const dropId = 'ms-drop-' + Math.random().toString(36).slice(2, 9);
  dropEl.id = dropId;
  searchEl.setAttribute('aria-controls', dropId);

  function memberById(id) {
    return members.find((m) => m.id === id);
  }

  function renderTeamBar() {
    if (!teams.length) {
      teamBarEl.hidden = true;
      return;
    }
    const parts = teams
      .map((t) => {
        const count = membersOfTeam(t.id).length;
        if (!count) return '';
        return (
          '<span class="member-ms-team-ctrl">' +
          '<span class="member-ms-team-label">' +
          escapeHtml(t.name) +
          ' <span class="text-muted">(' +
          count +
          ')</span></span>' +
          '<button type="button" class="btn btn-outline-primary btn-sm py-0 px-2" data-team-add="' +
          escapeHtml(t.id) +
          '" title="Incluir todo el equipo">+</button>' +
          '<button type="button" class="btn btn-outline-secondary btn-sm py-0 px-2" data-team-sub="' +
          escapeHtml(t.id) +
          '" title="Excluir todo el equipo">−</button></span>'
        );
      })
      .filter(Boolean);
    if (!parts.length) {
      teamBarEl.hidden = true;
      return;
    }
    teamBarEl.hidden = false;
    teamBarEl.innerHTML = '<span class="small text-muted">Equipos:</span>' + parts.join('');
    teamBarEl.querySelectorAll('[data-team-add]').forEach((btn) => {
      btn.addEventListener('click', () => {
        membersOfTeam(btn.getAttribute('data-team-add')).forEach((m) => selected.add(m.id));
        renderChips();
        renderDropdown();
      });
    });
    teamBarEl.querySelectorAll('[data-team-sub]').forEach((btn) => {
      btn.addEventListener('click', () => {
        membersOfTeam(btn.getAttribute('data-team-sub')).forEach((m) => selected.delete(m.id));
        renderChips();
        renderDropdown();
      });
    });
  }

  function renderChips() {
    if (!selected.size) {
      chipsEl.innerHTML = '<span class="text-muted small py-1 d-inline-block">Ningún destinatario seleccionado.</span>';
      return;
    }
    chipsEl.innerHTML = [...selected]
      .map((id) => {
        const m = memberById(id);
        if (!m) return '';
        return (
          '<span class="badge rounded-pill text-bg-light border member-ms-chip" role="listitem">' +
          escapeHtml(memberPickLabel(m, teamNames)) +
          '<button type="button" class="member-ms-chip-remove" data-rm="' +
          escapeHtml(id) +
          '" aria-label="Quitar destinatario">&times;</button></span>'
        );
      })
      .join('');
    chipsEl.querySelectorAll('[data-rm]').forEach((btn) => {
      btn.addEventListener('click', () => {
        selected.delete(btn.getAttribute('data-rm'));
        renderChips();
        renderDropdown();
      });
    });
  }

  function renderDropdown() {
    const q = searchEl.value.trim().toLowerCase();
    const available = members.filter((m) => {
      if (selected.has(m.id)) return false;
      if (!q) return true;
      const hay =
        memberPickLabel(m, teamNames).toLowerCase() + ' ' + (m.email || '').toLowerCase();
      return hay.includes(q);
    });
    if (!available.length) {
      dropEl.innerHTML =
        '<div class="list-group-item list-group-item-light small text-muted">' +
        (q ? 'Sin coincidencias.' : 'Todos los miembros ya están seleccionados.') +
        '</div>';
    } else {
      const limit = 40;
      const slice = available.slice(0, limit);
      dropEl.innerHTML = slice
        .map(
          (m) =>
            '<button type="button" class="list-group-item list-group-item-action py-2 member-ms-option" data-id="' +
            escapeHtml(m.id) +
            '">' +
            escapeHtml(memberPickLabel(m, teamNames)) +
            '</button>'
        )
        .join('');
      if (available.length > limit) {
        dropEl.innerHTML +=
          '<div class="list-group-item list-group-item-light small text-muted">+' +
          (available.length - limit) +
          ' más; afina la búsqueda.</div>';
      }
      dropEl.querySelectorAll('.member-ms-option').forEach((btn) => {
        btn.addEventListener('click', () => {
          selected.add(btn.getAttribute('data-id'));
          searchEl.value = '';
          renderChips();
          renderDropdown();
          searchEl.focus();
        });
      });
    }
    const open = document.activeElement === searchEl && !dropEl.hidden;
    if (open) dropEl.hidden = false;
  }

  function openDropdown() {
    dropEl.hidden = false;
    searchEl.setAttribute('aria-expanded', 'true');
    renderDropdown();
  }

  function closeDropdown() {
    dropEl.hidden = true;
    searchEl.setAttribute('aria-expanded', 'false');
  }

  searchEl.addEventListener('focus', openDropdown);
  searchEl.addEventListener('input', () => {
    openDropdown();
    renderDropdown();
  });
  searchEl.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      closeDropdown();
      searchEl.blur();
    }
  });
  document.addEventListener('click', (ev) => {
    if (!container.contains(ev.target)) closeDropdown();
  });

  container._memberMultiSelect = {
    getSelectedIds: () => [...selected],
    selectAll: () => {
      members.forEach((m) => selected.add(m.id));
      renderChips();
      renderDropdown();
    },
    selectNone: () => {
      selected.clear();
      renderChips();
      renderDropdown();
    },
    setSelectedIds: (ids) => {
      selected.clear();
      (ids || []).forEach((id) => selected.add(id));
      renderChips();
      renderDropdown();
    },
  };

  renderTeamBar();
  renderChips();
  closeDropdown();
}

function renderMemberPickList(container, members, options = {}) {
  mountMemberMultiSelect(container, members, options);
}

function getCheckedMemberIds(container) {
  if (container && container._memberMultiSelect) {
    return container._memberMultiSelect.getSelectedIds();
  }
  return [];
}

function wireSelectAll(noneBtn, allBtn, container) {
  if (!allBtn || !noneBtn || !container) return;
  allBtn.addEventListener('click', () => container._memberMultiSelect?.selectAll());
  noneBtn.addEventListener('click', () => container._memberMultiSelect?.selectNone());
}

async function openDispatchModal(campaignId, preselectedIds = null, resend = false) {
  pendingDispatchCampaignId = campaignId;
  pendingDispatchResend = resend;
  const modal = $('#dispatch-modal');
  const picks = $('#dispatch-member-picks');
  const statusEl = $('#dispatch-status');
  setStatus(statusEl, '');
  const bundle = await loadMembersBundle();
  const members = bundle.members;
  const selectedIds =
    preselectedIds === null ? members.map((m) => m.id) : preselectedIds && preselectedIds.length ? preselectedIds : [];
  renderMemberPickList(picks, members, { selectedIds, teams: bundle.teams });
  modal.showModal();
}

async function initCampaigns() {
  const form = $('#campaign-form');
  const statusEl = $('#campaign-form-status');
  const previewBtn = $('#camp-preview-btn');
  const previewCard = $('#camp-preview-card');

  previewBtn.addEventListener('click', async () => {
    setStatus(statusEl, 'Obteniendo vista previa…');
    try {
      const data = await api('/preview-post', {
        method: 'POST',
        admin: true,
        body: {
          url: $('#camp-url').value.trim(),
          repostParentUrn: $('#camp-urn').value.trim(),
        },
      });
      previewState = { preview: data.preview, urn: data.repostParentUrn };
      $('#camp-urn').value = data.repostParentUrn || '';
      const p = data.preview;
      previewCard.hidden = false;
      previewCard.innerHTML =
        (p.image ? '<img src="' + escapeHtml(p.image) + '" alt="" class="preview-img" />' : '') +
        '<strong>' +
        escapeHtml(p.title || 'Sin título') +
        '</strong><p class="meta">' +
        escapeHtml(p.description || '') +
        '</p>';
      setStatus(statusEl, 'Vista previa lista.', 'ok');
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });

  wireSelectAll($('#camp-select-none'), $('#camp-select-all'), $('#camp-member-picks'));

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const memberIds = getCheckedMemberIds($('#camp-member-picks'));
    if (!memberIds.length) {
      setStatus(statusEl, 'Elige al menos un miembro destino.', 'err');
      return;
    }
    setStatus(statusEl, 'Guardando…');
    try {
      const data = await api('/campaigns', {
        method: 'POST',
        admin: true,
        body: {
          title: $('#camp-title').value.trim(),
          linkedinUrl: $('#camp-url').value.trim(),
          repostParentUrn: $('#camp-urn').value.trim() || previewState.urn,
          commentary: $('#camp-commentary').value.trim(),
          preview: previewState.preview,
          memberIds,
        },
      });
      setStatus(statusEl, 'Campaña guardada. Enviando…', 'ok');
      await dispatchCampaign(data.campaign.id, memberIds, statusEl);
      form.reset();
      previewCard.hidden = true;
      previewState = { preview: {}, urn: '' };
      await refreshCampaignsList();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });

  $('#modal-close').addEventListener('click', () => $('#campaign-modal').close());
  document.querySelectorAll('.dispatch-modal-close').forEach((b) => b.addEventListener('click', () => $('#dispatch-modal').close()));
  wireSelectAll($('#dispatch-select-none'), $('#dispatch-select-all'), $('#dispatch-member-picks'));
  $('#dispatch-confirm').addEventListener('click', async () => {
    const statusEl = $('#dispatch-status');
    const memberIds = getCheckedMemberIds($('#dispatch-member-picks'));
    if (!pendingDispatchCampaignId || !memberIds.length) {
      setStatus(statusEl, 'Elige al menos un miembro.', 'err');
      return;
    }
    try {
      await dispatchCampaign(pendingDispatchCampaignId, memberIds, statusEl, pendingDispatchResend);
      $('#dispatch-modal').close();
      await refreshCampaigns();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
}

async function dispatchCampaign(id, memberIds, statusEl, resend = false) {
  setStatus(statusEl, 'Enviando invitaciones…');
  try {
    const data = await api('/dispatch', {
      method: 'POST',
      admin: true,
      body: { campaignId: id, memberIds, resend: resend || undefined },
    });
    setStatus(statusEl, 'Enviadas ' + data.sent + ' invitaciones a ' + memberIds.length + ' personas.', 'ok');
  } catch (e) {
    setStatus(statusEl, e.message, 'err');
    throw e;
  }
}

async function refreshCampaignMemberPicks() {
  const picks = $('#camp-member-picks');
  try {
    const bundle = await loadMembersBundle();
    renderMemberPickList(picks, bundle.members, { checkedByDefault: true, teams: bundle.teams });
    $('#camp-member-tools').hidden = !bundle.members.length;
  } catch (e) {
    if (picks) picks.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }
}

async function refreshCampaignsList() {
  const list = $('#campaigns-list');
  try {
    const campData = await api('/campaigns', { admin: true });
    const campaigns = campData.campaigns || [];
    if (!campaigns.length) {
      list.innerHTML = '<p class="empty">No hay campañas.</p>';
      return;
    }
    list.innerHTML =
      '<div class="table-responsive"><table class="table table-hover align-middle mb-0 campaign-history-table">' +
      '<thead class="table-light"><tr><th>Campaña</th><th>Fecha</th><th>Envíos</th><th>Reposts</th>' +
      '<th class="text-end" style="min-width:220px">Acciones</th></tr></thead><tbody>' +
      campaigns
        .map((c) => {
          const sent = (c.deliveries || []).length;
          const rep = (c.deliveries || []).filter((d) => d.action === 'approve').length;
          return (
            '<tr><td class="fw-semibold">' +
            escapeHtml(c.title) +
            '</td><td class="text-muted small">' +
            escapeHtml(formatDate(c.dispatchedAt || c.createdAt)) +
            '</td><td>' +
            sent +
            '</td><td>' +
            rep +
            '</td><td class="text-end"><div class="btn-group btn-group-sm" role="group">' +
            '<button type="button" class="btn btn-primary" data-send="' +
            escapeHtml(c.id) +
            '">Enviar</button>' +
            '<button type="button" class="btn btn-outline-secondary" data-resend="' +
            escapeHtml(c.id) +
            '">Reenviar</button>' +
            '<button type="button" class="btn btn-outline-secondary" data-detail="' +
            escapeHtml(c.id) +
            '">Detalle</button></div></td></tr>'
          );
        })
        .join('') +
      '</tbody></table></div>';
    list.querySelectorAll('[data-detail]').forEach((b) =>
      b.addEventListener('click', () => openCampaignDetail(b.getAttribute('data-detail')))
    );
    list.querySelectorAll('[data-send]').forEach((b) =>
      b.addEventListener('click', () => openDispatchModal(b.getAttribute('data-send')))
    );
    list.querySelectorAll('[data-resend]').forEach((b) =>
      b.addEventListener('click', () => openDispatchModal(b.getAttribute('data-resend'), null, true))
    );
  } catch (e) {
    list.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }
}

async function refreshCampaigns() {
  await refreshCampaignMemberPicks();
  await refreshCampaignsList();
}

async function initInvite() {
  const form = $('#invite-form');
  const statusEl = $('#invite-form-status');
  const box = $('#invite-result');
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    setStatus(statusEl, 'Generando enlace…');
    try {
      const data = await api('/connect-invite', {
        method: 'POST',
        admin: true,
        body: { name: $('#inv-name').value.trim(), email: $('#inv-email').value.trim() },
      });
      $('#invite-url').value = data.inviteUrl || '';
      $('#invite-oauth-url').value = data.linkedinConnectUrl || '';
      box.hidden = false;
      let msg = 'Enlace listo. Envíalo al empleado por email o Slack.';
      if (data.notice) msg += ' ' + data.notice;
      setStatus(statusEl, msg, data.linkedinConnectUrl ? 'ok' : '');
      await refreshMembers();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
  $('#copy-invite-url').addEventListener('click', () => {
    navigator.clipboard.writeText($('#invite-url').value);
    setStatus(statusEl, 'Enlace Ngaged copiado.', 'ok');
  });
  $('#copy-oauth-url').addEventListener('click', () => {
    navigator.clipboard.writeText($('#invite-oauth-url').value);
    setStatus(statusEl, 'Enlace OAuth copiado.', 'ok');
  });
}

async function initMembers() {
  const form = $('#member-form');
  const statusEl = $('#member-form-status');
  const connEl = $('#mem-connections');

  try {
    const connections = await loadConnections();
    connEl.innerHTML = connections.length
      ? '<div class="chips">' +
        connections
          .map(
            (c) =>
              '<button type="button" class="chip chip-btn" data-pid="' +
              escapeHtml(c.platformId) +
              '">' +
              escapeHtml(c.username || c.platformId) +
              '</button>'
          )
          .join('') +
        '</div>'
      : '<p class="meta">Usa «Invitar a vincular LinkedIn» arriba o conecta cuentas en el panel de canales.</p>';
    connEl.querySelectorAll('.chip-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        $('#mem-platform').value = btn.getAttribute('data-pid');
      });
    });
  } catch (e) {
    connEl.innerHTML = '<p class="meta">' + escapeHtml(e.message) + '</p>';
  }

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    setStatus(statusEl, 'Guardando…');
    try {
      await api('/members', {
        method: 'POST',
        admin: true,
        body: {
          name: $('#mem-name').value.trim(),
          email: $('#mem-email').value.trim(),
          platformId: $('#mem-platform').value.trim(),
          teamId: $('#mem-team').value.trim(),
        },
      });
      form.reset();
      setStatus(statusEl, 'Miembro añadido.', 'ok');
      await refreshMembers();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
}

function renderTeamsBadges(teams) {
  const list = $('#teams-list');
  if (!list) return;
  list.innerHTML =
    (teams || [])
      .map((t) => '<span class="badge text-bg-light border">' + escapeHtml(t.name) + '</span>')
      .join('') || '<span class="text-muted small">Sin equipos.</span>';
}

function fillTeamSelect(teams, selectEl) {
  if (!selectEl) return;
  const cur = selectEl.value;
  selectEl.innerHTML =
    '<option value="">Sin equipo</option>' +
    (teams || [])
      .map(
        (t) =>
          '<option value="' + escapeHtml(t.id) + '">' + escapeHtml(t.name) + '</option>'
      )
      .join('');
  if (cur) selectEl.value = cur;
}

function initTeams() {
  const form = $('#team-form');
  const statusEl = $('#team-form-status');
  if (!form) return;
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const name = $('#team-name').value.trim();
    if (!name) return;
    setStatus(statusEl, 'Creando equipo…');
    try {
      await api('/teams', { method: 'POST', admin: true, body: { name } });
      $('#team-name').value = '';
      setStatus(statusEl, 'Equipo creado.', 'ok');
      await refreshMembers();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });
}

async function refreshMembers() {
  const list = $('#members-list');
  try {
    const data = await api('/members', { admin: true });
    const members = data.members || [];
    const teams = data.teams || [];
    renderTeamsBadges(teams);
    fillTeamSelect(teams, $('#mem-team'));
    const tmap = teamNameMap(teams);
    let connections = [];
    try {
      connections = await loadConnections();
    } catch {
      connections = [];
    }
    if (!members.length) {
      list.innerHTML = '<p class="empty">Sin miembros.</p>';
      return;
    }
    const linkOptions =
      connections.length > 0
        ? connections
            .map(
              (c) =>
                '<option value="' +
                escapeHtml(c.platformId) +
                '">' +
                escapeHtml(c.username || c.platformId) +
                '</option>'
            )
            .join('')
        : '';
    list.innerHTML =
      '<div class="list-group list-group-flush member-directory">' +
      members
        .map((m) => {
          const st = m.connectStatus || (m.platformId ? 'linked' : 'pending');
          const pending = !m.platformId;
          const linkSelect =
            pending && linkOptions
              ? '<select class="form-select form-select-sm mt-2 member-link-select" data-link="' +
                escapeHtml(m.id) +
                '"><option value="">Vincular cuenta LinkedIn…</option>' +
                linkOptions +
                '</select>'
              : '';
          const teamSelect =
            '<label class="small text-muted mt-2 mb-0">Equipo</label><select class="form-select form-select-sm member-team-select" data-member="' +
            escapeHtml(m.id) +
            '"><option value="">Sin equipo</option>' +
            teams
              .map(
                (t) =>
                  '<option value="' +
                  escapeHtml(t.id) +
                  '"' +
                  ((m.teamId || '') === t.id ? ' selected' : '') +
                  '>' +
                  escapeHtml(t.name) +
                  '</option>'
              )
              .join('') +
            '</select>';
          return (
            '<div class="list-group-item"><div class="d-flex flex-wrap justify-content-between align-items-start gap-2">' +
            '<div class="flex-grow-1"><div class="fw-semibold">' +
            escapeHtml(m.name || m.email) +
            '</div><div class="small text-muted">' +
            escapeHtml(m.email) +
            '</div><div class="small text-muted">' +
            escapeHtml(m.platformId || 'Sin LinkedIn') +
            ' · <span class="badge text-bg-light border">' +
            escapeHtml(st) +
            '</span>' +
            (m.teamId && tmap[m.teamId]
              ? ' · <span class="badge member-team-badge">' + escapeHtml(tmap[m.teamId]) + '</span>'
              : '') +
            '</div>' +
            teamSelect +
            linkSelect +
            '</div>' +
            '<div class="btn-group btn-group-sm flex-shrink-0" role="group">' +
            '<button type="button" class="btn btn-outline-secondary" data-invite="' +
            escapeHtml(m.id) +
            '">Enlace</button>' +
            '<button type="button" class="btn btn-outline-secondary" data-sync="' +
            escapeHtml(m.id) +
            '">Sync</button>' +
            '<button type="button" class="btn btn-outline-danger" data-del="' +
            escapeHtml(m.id) +
            '">Eliminar</button></div></div></div>'
          );
        })
        .join('') +
      '</div>';
    list.querySelectorAll('.member-team-select').forEach((sel) => {
      sel.addEventListener('change', async () => {
        try {
          await api('/members', {
            method: 'PUT',
            admin: true,
            body: { id: sel.getAttribute('data-member'), teamId: sel.value },
          });
          await refreshMembers();
          await refreshCampaignMemberPicks();
        } catch (e) {
          alert(e.message);
        }
      });
    });
    list.querySelectorAll('.member-link-select').forEach((sel) => {
      sel.addEventListener('change', async () => {
        const platformId = sel.value;
        if (!platformId) return;
        const memberId = sel.getAttribute('data-link');
        try {
          await api('/members', { method: 'PUT', admin: true, body: { id: memberId, platformId } });
          await refreshMembers();
        } catch (e) {
          alert(e.message);
          sel.value = '';
        }
      });
    });
    list.querySelectorAll('[data-invite]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const label = btn.textContent;
        btn.disabled = true;
        try {
          const data = await api('/connect-invite', {
            method: 'POST',
            admin: true,
            body: { memberId: btn.getAttribute('data-invite') },
          });
          const url = data.inviteUrl || '';
          const inviteUrlEl = $('#invite-url');
          const inviteOauthEl = $('#invite-oauth-url');
          if (inviteUrlEl) inviteUrlEl.value = url;
          if (inviteOauthEl) inviteOauthEl.value = data.linkedinConnectUrl || '';
          const inviteResult = $('#invite-result');
          if (inviteResult) inviteResult.hidden = false;
          if (url) {
            await navigator.clipboard.writeText(url);
          }
          btn.textContent = 'Copiado';
          btn.classList.remove('btn-outline-secondary');
          btn.classList.add('btn-success');
          setTimeout(() => {
            btn.textContent = label;
            btn.classList.add('btn-outline-secondary');
            btn.classList.remove('btn-success');
            btn.disabled = false;
          }, 2000);
          await refreshMembers();
        } catch (e) {
          btn.disabled = false;
          alert(e.message);
        }
      });
    });
    list.querySelectorAll('[data-sync]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          const data = await api('/members-sync', {
            method: 'POST',
            admin: true,
            body: { memberId: btn.getAttribute('data-sync') },
          });
          alert('LinkedIn: ' + (data.platformId || 'OK'));
          await refreshMembers();
        } catch (e) {
          alert(e.message);
        }
      });
    });
    list.querySelectorAll('[data-del]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (!confirm('¿Eliminar miembro?')) return;
        await api('/members', { method: 'DELETE', admin: true, body: { id: btn.getAttribute('data-del') } });
        await refreshMembers();
      });
    });
  } catch (e) {
    list.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }
}

function renderMemberConnections(container, connections) {
  container.innerHTML = '';
  if (!connections.length) {
    container.innerHTML = '<p class="empty">No hay cuentas LinkedIn disponibles.</p>';
    return;
  }
  const wrap = document.createElement('div');
  wrap.className = 'chips';
  connections.forEach((c) => {
    const label = document.createElement('label');
    label.className = 'chip';
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = 'memberPlatform';
    input.value = c.platformId;
    if (localStorage.getItem(MEMBER_PLATFORM_STORAGE) === c.platformId) input.checked = true;
    label.appendChild(input);
    label.appendChild(document.createTextNode(c.username || c.platformId));
    wrap.appendChild(label);
  });
  container.appendChild(wrap);
}

async function refreshMemberQueue() {
  const picker = $('#member-accounts');
  const listEl = $('#member-pending');
  const statusEl = $('#member-status');
  let connections = [];
  try {
    connections = await loadConnections();
    renderMemberConnections(picker, connections);
    picker.addEventListener('change', () => {
      const selected = picker.querySelector('input:checked');
      if (selected) localStorage.setItem(MEMBER_PLATFORM_STORAGE, selected.value);
      loadPending();
    });
  } catch (e) {
    picker.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }

  async function loadPending() {
    const platformId =
      picker.querySelector('input:checked')?.value || localStorage.getItem(MEMBER_PLATFORM_STORAGE) || '';
    if (!platformId) {
      listEl.innerHTML = '<p class="empty">Elige tu cuenta LinkedIn.</p>';
      return;
    }
    try {
      const data = await api('/member-queue?platformId=' + encodeURIComponent(platformId));
      const pending = data.pending || [];
      if (!pending.length) {
        listEl.innerHTML = '<p class="empty">No tienes campañas pendientes.</p>';
        return;
      }
      listEl.innerHTML = pending
        .map((p) => {
          const cardId = 'p-' + p.campaignId;
          return (
            '<article class="activity" id="' +
            cardId +
            '"><h3>' +
            escapeHtml(p.title) +
            '</h3><p>' +
            escapeHtml(p.preview?.description || p.commentary || '') +
            '</p><div class="row"><button type="button" class="btn btn-primary" data-act="approve">Repostear</button><button type="button" class="btn btn-secondary" data-act="decline">Ignorar</button></div><div class="status" hidden></div></article>'
          );
        })
        .join('');
      listEl.querySelectorAll('.activity').forEach((card, i) => {
        const item = pending[i];
        card.querySelectorAll('button').forEach((btn) => {
          btn.addEventListener('click', async () => {
            const st = card.querySelector('.status');
            setStatus(st, 'Procesando…');
            st.hidden = false;
            try {
              await api('/member-respond', {
                method: 'POST',
                body: {
                  campaignId: item.campaignId,
                  memberId: item.memberId,
                  platformId,
                  action: btn.getAttribute('data-act'),
                },
              });
              setStatus(st, btn.getAttribute('data-act') === 'approve' ? '¡Publicado!' : 'Ignorado.', 'ok');
              card.querySelectorAll('button').forEach((b) => (b.disabled = true));
            } catch (e) {
              setStatus(st, e.message, 'err');
            }
          });
        });
      });
      setStatus(statusEl, '');
    } catch (e) {
      listEl.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
    }
  }

  await loadPending();
}

document.addEventListener('DOMContentLoaded', async () => {
  initMobileNav();
  initNav();
  initAdminAuthUi();
  initAdminUsersPanel();
  try {
    await ensureAdminSession();
  } catch {
    return;
  }
  initDashboardControls();
  initCampaigns();
  initInvite();
  initMembers();
  initTeams();
  initSettingsPanel();
  loadWorkspaceBadge();
  $('#connections-refresh')?.addEventListener('click', refreshConnectionsTable);
  navigateTo('dashboard');
});
