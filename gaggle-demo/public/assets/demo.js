const API = '/api';
const ADMIN_KEY_STORAGE = 'gaggle_demo_admin_key';
const MEMBER_PLATFORM_STORAGE = 'gaggle_demo_platform_id';

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

function renderConnections(container, connections, { selectable = false, name = 'platform' } = {}) {
  container.innerHTML = '';
  if (!connections.length) {
    container.innerHTML = '<p class="empty">No hay conexiones LinkedIn en Publora.</p>';
    return;
  }
  const wrap = document.createElement('div');
  wrap.className = 'chips';
  connections.forEach((c) => {
    const label = document.createElement('label');
    label.className = 'chip';
    const input = document.createElement('input');
    input.type = selectable ? 'checkbox' : 'radio';
    input.name = name;
    input.value = c.platformId;
    if (!selectable && localStorage.getItem(MEMBER_PLATFORM_STORAGE) === c.platformId) {
      input.checked = true;
    }
    label.appendChild(input);
    label.appendChild(document.createTextNode(c.username || c.platformId));
    wrap.appendChild(label);
  });
  container.appendChild(wrap);
}

async function loadConnections() {
  const data = await api('/connections');
  return data.connections || [];
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
    });
  });
}

function activityLabel(a) {
  const type = a.type === 'repost' ? 'Repost LinkedIn' : 'Post LinkedIn';
  return type + ' · ' + (a.title || a.id);
}

function renderActivities(listEl, activities, { member = false, platformId = '' } = {}) {
  listEl.innerHTML = '';
  if (!activities.length) {
    listEl.innerHTML = '<p class="empty">No hay actividades abiertas.</p>';
    return;
  }
  activities.forEach((a) => {
    const card = document.createElement('article');
    card.className = 'activity';
    const targets = (a.targetPlatformIds || []).length
      ? 'Audiencia: ' + a.targetPlatformIds.join(', ')
      : 'Audiencia: cualquier cuenta conectada';
    card.innerHTML =
      '<h3>' +
      escapeHtml(a.title) +
      '</h3>' +
      '<div class="meta">' +
      escapeHtml(activityLabel(a)) +
      ' · ' +
      escapeHtml(targets) +
      '</div>' +
      (a.content ? '<p>' + escapeHtml(a.content) + '</p>' : '') +
      (a.repostParentUrn ? '<p class="meta">URN: ' + escapeHtml(a.repostParentUrn) + '</p>' : '');

    if (member) {
      const row = document.createElement('div');
      row.className = 'row';
      const approve = document.createElement('button');
      approve.className = 'btn btn-primary';
      approve.textContent = 'Compartir ahora';
      approve.type = 'button';
      approve.addEventListener('click', () => respond(a.id, 'approve', platformId, card));
      const decline = document.createElement('button');
      decline.className = 'btn btn-secondary';
      decline.textContent = 'No gracias';
      decline.type = 'button';
      decline.addEventListener('click', () => respond(a.id, 'decline', platformId, card));
      row.append(approve, decline);
      card.appendChild(row);
      const status = document.createElement('div');
      status.hidden = true;
      card.appendChild(status);
    }

    listEl.appendChild(card);
  });
}

async function respond(activityId, action, platformId, card) {
  const statusEl = card.querySelector('.status') || card.lastElementChild;
  if (!platformId) {
    setStatus(statusEl, 'Elige tu cuenta LinkedIn arriba.', 'err');
    statusEl.hidden = false;
    return;
  }
  setStatus(statusEl, action === 'approve' ? 'Publicando…' : 'Registrando…');
  statusEl.hidden = false;
  try {
    const data = await api('/respond', {
      method: 'POST',
      body: { activityId, platformId, action },
    });
    const msg =
      action === 'approve'
        ? 'Publicado vía Publora. postGroupId: ' + (data.response?.postGroupId || '—')
        : 'Actividad rechazada.';
    setStatus(statusEl, msg, 'ok');
    card.querySelectorAll('button').forEach((b) => (b.disabled = true));
  } catch (e) {
    setStatus(statusEl, e.message, 'err');
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function initAdmin() {
  const adminKeyInput = $('#admin-key');
  const saveKeyBtn = $('#save-admin-key');
  const targetsEl = $('#admin-targets');
  const statusEl = $('#admin-status');
  const listEl = $('#admin-activities-list');
  const form = $('#admin-form');

  adminKeyInput.value = localStorage.getItem(ADMIN_KEY_STORAGE) || '';
  saveKeyBtn.addEventListener('click', () => {
    localStorage.setItem(ADMIN_KEY_STORAGE, adminKeyInput.value.trim());
    setStatus(statusEl, 'Clave admin guardada en este navegador.', 'ok');
  });

  let connections = [];
  try {
    connections = await loadConnections();
    renderConnections(targetsEl, connections, { selectable: true, name: 'targets' });
  } catch (e) {
    targetsEl.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }

  async function refreshAdminList() {
    try {
      const data = await api('/activities');
      renderActivities(listEl, data.activities || [], { member: false });
    } catch (e) {
      listEl.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
    }
  }

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    setStatus(statusEl, 'Creando actividad…');
    const type = $('#activity-type').value;
    const targetPlatformIds = [...targetsEl.querySelectorAll('input:checked')].map((i) => i.value);
    try {
      await api('/activities', {
        method: 'POST',
        admin: true,
        body: {
          title: $('#activity-title').value.trim(),
          type,
          content: $('#activity-content').value.trim(),
          repostParentUrn: $('#activity-urn').value.trim(),
          targetPlatformIds,
        },
      });
      form.reset();
      setStatus(statusEl, 'Actividad creada.', 'ok');
      await refreshAdminList();
    } catch (e) {
      setStatus(statusEl, e.message, 'err');
    }
  });

  $('#activity-type').addEventListener('change', (e) => {
    $('#urn-field').hidden = e.target.value !== 'repost';
  });

  await refreshAdminList();
}

async function initMember() {
  const picker = $('#member-accounts');
  const listEl = $('#member-activities');
  const statusEl = $('#member-status');

  let connections = [];
  try {
    connections = await loadConnections();
    renderConnections(picker, connections, { selectable: false, name: 'memberPlatform' });
    picker.addEventListener('change', () => {
      const selected = picker.querySelector('input:checked');
      if (selected) {
        localStorage.setItem(MEMBER_PLATFORM_STORAGE, selected.value);
      }
      refreshMember();
    });
  } catch (e) {
    picker.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
  }

  async function refreshMember() {
    const platformId =
      picker.querySelector('input:checked')?.value || localStorage.getItem(MEMBER_PLATFORM_STORAGE) || '';
    try {
      const data = await api('/activities');
      renderActivities(listEl, data.activities || [], { member: true, platformId });
      setStatus(statusEl, '');
    } catch (e) {
      listEl.innerHTML = '<p class="empty">' + escapeHtml(e.message) + '</p>';
    }
  }

  await refreshMember();
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initAdmin();
  initMember();
});
