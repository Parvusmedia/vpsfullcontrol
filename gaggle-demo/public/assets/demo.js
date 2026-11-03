const API = '/api';
const ADMIN_KEY_STORAGE = 'ngaged_admin_key';
const MEMBER_PLATFORM_STORAGE = 'ngaged_platform_id';
let dashDays = 7;
let chartInstances = {};

function $(sel, root = document) {
  return root.querySelector(sel);
}

function setStatus(el, message, kind = '') {
  if (!el) return;
  el.textContent = message || '';
  el.className = 'status' + (kind ? ' ' + kind : '');
  el.hidden = !message;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.admin) {
    headers['X-Demo-Admin-Key'] = localStorage.getItem(ADMIN_KEY_STORAGE) || '';
  }
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || res.statusText || 'Request failed');
  }
  return data;
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

function initTabs() {
  const tabs = document.querySelectorAll('[data-tab]');
  const panels = document.querySelectorAll('[data-panel]');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const id = tab.getAttribute('data-tab');
      tabs.forEach((t) => t.classList.toggle('is-active', t === tab));
      panels.forEach((p) => {
        p.hidden = p.getAttribute('data-panel') !== id;
      });
      if (id === 'dashboard') loadDashboard();
      if (id === 'campaigns') refreshCampaigns();
      if (id === 'members') refreshMembers();
      if (id === 'member') refreshMemberQueue();
    });
  });
  document.querySelectorAll('[data-goto]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-goto');
      document.querySelector('[data-tab="' + id + '"]')?.click();
    });
  });
}

function initAdminKey() {
  const input = $('#admin-key');
  const saveBtn = $('#save-admin-key');
  const global = $('#global-status');
  if (!localStorage.getItem(ADMIN_KEY_STORAGE)) {
    const legacy = localStorage.getItem('gaggle_demo_admin_key');
    if (legacy) localStorage.setItem(ADMIN_KEY_STORAGE, legacy);
  }
  input.value = localStorage.getItem(ADMIN_KEY_STORAGE) || '';
  saveBtn.addEventListener('click', async () => {
    const key = input.value.trim();
    localStorage.setItem(ADMIN_KEY_STORAGE, key);
    setStatus(global, 'Comprobando clave…');
    try {
      await api('/stats?days=7', { admin: true });
      setStatus(global, 'Clave correcta. Guardada en este navegador.', 'ok');
      loadDashboard();
    } catch (e) {
      localStorage.removeItem(ADMIN_KEY_STORAGE);
      setStatus(global, e.message, 'err');
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
    .map(
      (c) =>
        '<div class="kpi-card' +
        (c.hero ? ' kpi-hero' : '') +
        '"><div class="kpi-label">' +
        escapeHtml(c.label) +
        '</div><div class="kpi-value">' +
        escapeHtml(String(c.value)) +
        '</div>' +
        (c.sub ? '<div class="kpi-sub">' + escapeHtml(c.sub) + '</div>' : '') +
        '</div>'
    )
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
    options: { animation: { duration: 400 }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
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
      indexAxis: 'y',
      animation: { duration: 400 },
      plugins: { legend: { display: false } },
    },
  });
}

function renderRecentTable(rows) {
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
        '%</td><td><button type="button" class="btn btn-secondary btn-sm" data-detail="' +
        escapeHtml(r.id) +
        '">Detalle</button></td></tr>'
    )
    .join('');
  tbody.querySelectorAll('[data-detail]').forEach((btn) => {
    btn.addEventListener('click', () => openCampaignDetail(btn.getAttribute('data-detail')));
  });
}

async function loadDashboard() {
  const empty = $('#dash-empty');
  const content = $('#dash-content');
  try {
    const q = dashDays === 'all' || dashDays === 0 ? 'all' : String(dashDays);
    const data = await api('/stats?days=' + encodeURIComponent(q), { admin: true });
    const hasData = (data.totals?.invitesSent ?? 0) > 0 || (data.totals?.campaigns ?? 0) > 0;
    empty.hidden = hasData;
    content.hidden = !hasData;
    if (!hasData) return;
    renderKpis(data.totals);
    renderCharts(data);
    renderRecentTable(data.recentCampaigns || []);
  } catch (e) {
    empty.hidden = false;
    content.hidden = true;
    empty.querySelector('p').textContent = e.message.includes('Admin') ? 'Guarda la clave admin arriba.' : e.message;
  }
}

function initDashboardControls() {
  document.querySelectorAll('.period-pills .pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.period-pills .pill').forEach((p) => p.classList.remove('is-active'));
      pill.classList.add('is-active');
      const d = pill.getAttribute('data-days');
      dashDays = d === 'all' ? 'all' : parseInt(d, 10);
      loadDashboard();
    });
  });
  $('#dash-refresh').addEventListener('click', loadDashboard);
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

function renderMemberPickList(container, members, { checkedByDefault = false } = {}) {
  if (!members.length) {
    container.innerHTML = '<p class="empty">Añade miembros en la pestaña Miembros (invitación o manual).</p>';
    return;
  }
  container.innerHTML = members
    .map((m) => {
      const label = (m.name || m.email) + (m.platformId ? '' : ' · sin LinkedIn');
      return (
        '<label class="member-row"><input type="checkbox" value="' +
        escapeHtml(m.id) +
        '"' +
        (checkedByDefault ? ' checked' : '') +
        ' /><span>' +
        escapeHtml(label) +
        '</span></label>'
      );
    })
    .join('');
}

function getCheckedMemberIds(container) {
  return [...container.querySelectorAll('input[type=checkbox]:checked')].map((i) => i.value);
}

function wireSelectAll(noneBtn, allBtn, container) {
  if (!allBtn || !noneBtn || !container) return;
  allBtn.addEventListener('click', () => container.querySelectorAll('input[type=checkbox]').forEach((i) => (i.checked = true)));
  noneBtn.addEventListener('click', () => container.querySelectorAll('input[type=checkbox]').forEach((i) => (i.checked = false)));
}

async function openDispatchModal(campaignId, preselectedIds = null, resend = false) {
  pendingDispatchCampaignId = campaignId;
  pendingDispatchResend = resend;
  const modal = $('#dispatch-modal');
  const picks = $('#dispatch-member-picks');
  const statusEl = $('#dispatch-status');
  setStatus(statusEl, '');
  const memData = await api('/members', { admin: true });
  const members = memData.members || [];
  renderMemberPickList(picks, members, { checkedByDefault: preselectedIds === null });
  if (preselectedIds && preselectedIds.length) {
    picks.querySelectorAll('input').forEach((i) => {
      i.checked = preselectedIds.includes(i.value);
    });
  }
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
      await refreshCampaigns();
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

async function refreshCampaigns() {
  const list = $('#campaigns-list');
  const picks = $('#camp-member-picks');
  try {
    const [campData, memData] = await Promise.all([
      api('/campaigns', { admin: true }),
      api('/members', { admin: true }),
    ]);
    const members = memData.members || [];
    renderMemberPickList(picks, members, { checkedByDefault: true });
    $('#camp-member-tools').hidden = !members.length;

    const campaigns = campData.campaigns || [];
    if (!campaigns.length) {
      list.innerHTML = '<p class="empty">No hay campañas.</p>';
      return;
    }
    list.innerHTML = campaigns
      .map((c) => {
        const sent = (c.deliveries || []).length;
        const rep = (c.deliveries || []).filter((d) => d.action === 'approve').length;
        return (
          '<article class="activity"><h3>' +
          escapeHtml(c.title) +
          '</h3><div class="meta">' +
          escapeHtml(formatDate(c.dispatchedAt || c.createdAt)) +
          ' · ' +
          sent +
          ' envíos · ' +
          rep +
          ' reposts</div><div class="row"><button type="button" class="btn btn-primary btn-sm" data-send="' +
          escapeHtml(c.id) +
          '">Enviar</button><button type="button" class="btn btn-secondary btn-sm" data-resend="' +
          escapeHtml(c.id) +
          '">Reenviar</button><button type="button" class="btn btn-secondary btn-sm" data-detail="' +
          escapeHtml(c.id) +
          '">Detalle</button></div></article>'
        );
      })
      .join('');
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

async function refreshMembers() {
  const list = $('#members-list');
  try {
    const data = await api('/members', { admin: true });
    const members = data.members || [];
    if (!members.length) {
      list.innerHTML = '<p class="empty">Sin miembros.</p>';
      return;
    }
    list.innerHTML = members
      .map((m) => {
        const st = m.connectStatus || (m.platformId ? 'linked' : 'pending');
        return (
          '<article class="activity"><h3>' +
          escapeHtml(m.name || m.email) +
          '</h3><div class="meta">' +
          escapeHtml(m.email) +
          '<br/>' +
          escapeHtml(m.platformId || 'Sin LinkedIn') +
          ' · ' +
          escapeHtml(st) +
          '</div><div class="row"><button type="button" class="btn btn-secondary btn-sm" data-invite="' +
          escapeHtml(m.id) +
          '">Regenerar enlace</button><button type="button" class="btn btn-secondary btn-sm" data-sync="' +
          escapeHtml(m.id) +
          '">Sync LinkedIn</button><button type="button" class="btn btn-danger btn-sm" data-del="' +
          escapeHtml(m.id) +
          '">Eliminar</button></div></article>'
        );
      })
      .join('');
    list.querySelectorAll('[data-invite]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          const data = await api('/connect-invite', {
            method: 'POST',
            admin: true,
            body: { memberId: btn.getAttribute('data-invite') },
          });
          $('#invite-url').value = data.inviteUrl || '';
          $('#invite-oauth-url').value = data.linkedinConnectUrl || '';
          $('#invite-result').hidden = false;
          alert(data.linkedinConnectUrl ? 'Enlaces regenerados (ver bloque Invitar).' : (data.notice || 'Enlace Ngaged regenerado.'));
          await refreshMembers();
        } catch (e) {
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

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initAdminKey();
  initDashboardControls();
  initCampaigns();
  initInvite();
  initMembers();
  loadDashboard();
});
