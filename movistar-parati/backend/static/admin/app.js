const toastEl = document.getElementById("toast");
let catalog = [];
let dashboard = null;
let activeAlerts = [];
let refreshTimer = null;

function headers() {
  return { "Content-Type": "application/json" };
}

function fetchOpts(options = {}) {
  return { credentials: "same-origin", ...options, headers: { ...headers(), ...(options.headers || {}) } };
}

function showToast(message, type = "ok") {
  toastEl.textContent = message;
  toastEl.className = `toast ${type}`;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.add("hidden"), 5000);
}

function fmtMoney(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${Number(v).toFixed(0)} €/mes`;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function api(path, options = {}) {
  const res = await fetch(path, fetchOpts(options));
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

function setConnected(ok) {
  const pill = document.getElementById("connStatus");
  pill.textContent = ok ? "Sincronizado con NocoDB" : "Sin conexión";
  pill.classList.toggle("ok", ok);
  if (ok) {
    clearInterval(refreshTimer);
    refreshTimer = setInterval(() => load({ quiet: true }), 30000);
  } else {
    clearInterval(refreshTimer);
  }
}

function switchView(name) {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
}

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.onclick = () => switchView(btn.dataset.view);
});

document.getElementById("refreshNow").onclick = () => load();
document.getElementById("pollNow").onclick = async () => {
  try {
    const result = await api("/api/movistar/admin/poll", { method: "POST" });
    showToast(`Detección OK · ${result.changes} cambios · ${result.notifications} notificaciones`);
    await load({ quiet: true });
  } catch (e) {
    showToast(e.message, "err");
  }
};

function renderStats() {
  if (!dashboard) return;
  document.getElementById("stats").innerHTML = `
    <div class="metric"><span>Productos activos</span><strong>${dashboard.products_active}</strong></div>
    <div class="metric"><span>En NocoDB total</span><strong>${dashboard.products_total}</strong></div>
    <div class="metric"><span>Ofertas destacadas</span><strong>${dashboard.featured}</strong></div>
    <div class="metric"><span>Novedades</span><strong>${dashboard.new_products}</strong></div>
    <div class="metric"><span>Avisos activos</span><strong>${dashboard.alerts_active}</strong></div>
  `;
  document.getElementById("nocodbLink").href = dashboard.nocodb_products_url;
  if (dashboard.sync_note) {
    document.getElementById("syncNote").textContent = dashboard.sync_note;
  }
}

function productAlertCounts() {
  const counts = {};
  for (const a of activeAlerts) {
    const pid = a.product_id;
    if (!pid) continue;
    counts[pid] = (counts[pid] || 0) + 1;
  }
  return counts;
}

function thumbHtml(p) {
  const initials = esc((p.brand || "?").slice(0, 2).toUpperCase());
  return `<div class="thumb-wrap">
    <div class="thumb-fallback" aria-hidden="true">${initials}</div>
    <img class="thumb" src="${esc(p.image_api_url)}" alt="${esc(p.display_name)}" loading="lazy" onerror="this.classList.add('broken')" />
  </div>`;
}

function filteredCatalog() {
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  const brand = document.getElementById("brandFilter").value;
  const activeOnly = document.getElementById("activeOnly").checked;
  const alertsOnly = document.getElementById("alertsOnly").checked;
  const alertCounts = productAlertCounts();
  return catalog.filter((p) => {
    if (activeOnly && !p.active) return false;
    if (alertsOnly && !alertCounts[p.id]) return false;
    if (brand && p.brand !== brand) return false;
    if (!q) return true;
    const hay = `${p.id} ${p.brand} ${p.name} ${p.display_name} ${p.record_id}`.toLowerCase();
    return hay.includes(q);
  });
}

function productEditForm(p) {
  return `
    <form class="product-edit" data-record="${esc(p.record_id)}">
      <label>Cuota €/mes
        <input type="number" name="monthly_price" value="${p.monthly_price ?? ""}" min="0" step="1" />
      </label>
      <label>Cuota anterior
        <input type="number" name="previous_monthly_price" value="${p.previous_monthly_price ?? ""}" min="0" step="1" />
      </label>
      <label>Precio total €
        <input type="number" name="price" value="${p.price ?? ""}" min="0" step="1" />
      </label>
      <label>Promoción
        <input type="text" name="promotion" value="${esc(p.promotion || "")}" />
      </label>
      <label>Regalo
        <input type="text" name="gift" value="${esc(p.gift || "")}" />
      </label>
      <div class="checks">
        <label><input type="checkbox" name="active" ${p.active ? "checked" : ""} /> Activo</label>
        <label><input type="checkbox" name="featured" ${p.featured ? "checked" : ""} /> Destacado</label>
        <label><input type="checkbox" name="is_new" ${p.is_new ? "checked" : ""} /> Nuevo</label>
      </div>
      <div class="row-actions">
        <button type="submit" class="action-btn">💾 Guardar en NocoDB</button>
        <a href="${esc(p.nocodb_row_url || dashboard?.nocodb_products_url || "#")}" target="_blank" rel="noopener">Abrir tabla CMS ↗</a>
      </div>
    </form>`;
}

function renderCatalog() {
  const items = filteredCatalog();
  const alertCounts = productAlertCounts();
  const box = document.getElementById("catalogTable");
  if (!items.length) {
    box.innerHTML = `<div class="empty">No hay productos que coincidan con el filtro.</div>`;
    return;
  }
  box.innerHTML = items.map((p) => {
    const alertCount = alertCounts[p.id] || 0;
    const badges = [
      p.active ? `<span class="badge">Activo</span>` : `<span class="badge inactive">Inactivo</span>`,
      p.featured ? `<span class="badge featured">Destacado</span>` : "",
      p.is_new ? `<span class="badge new">Nuevo</span>` : "",
      alertCount ? `<span class="badge alerts">🔔 ${alertCount} aviso${alertCount > 1 ? "s" : ""}</span>` : "",
      `<span class="badge">${esc(p.brand)}</span>`,
      `<span class="badge">#${esc(p.record_id)}</span>`,
    ].join("");
    const actions = (p.demo_actions || []).map((a) =>
      `<button type="button" class="action-btn sim-btn" data-id="${esc(p.id)}" data-price="${a.new_monthly}">${esc(a.label)}</button>`
    ).join("");
    const prev = p.previous_monthly_price && p.previous_monthly_price > p.monthly_price
      ? `<div class="prev">${fmtMoney(p.previous_monthly_price)}</div>` : "";
    return `
      <article class="product-row ${p.active ? "" : "inactive"}${alertCount ? " has-alerts" : ""}" data-id="${esc(p.id)}">
        ${thumbHtml(p)}
        <div class="product-main">
          <strong>${esc(p.display_name)}</strong>
          <div class="product-meta">ID: <code>${esc(p.id)}</code> · slug: <code>${esc(p.slug || p.id)}</code></div>
          <div class="badges">${badges}</div>
        </div>
        <div class="price-block">
          <div class="current">${fmtMoney(p.monthly_price)}</div>
          ${prev}
          <div class="product-meta">${p.price ? `${Number(p.price).toFixed(0)} € total` : ""}</div>
        </div>
        <div class="actions">${actions || `<span class="product-meta">—</span>`}</div>
        ${productEditForm(p)}
      </article>`;
  }).join("");

  box.querySelectorAll(".sim-btn").forEach((btn) => {
    btn.onclick = async () => {
      btn.disabled = true;
      try {
        const result = await api(`/api/movistar/admin/simulate-drop/${btn.dataset.id}?new_monthly=${btn.dataset.price}`, { method: "POST" });
        showToast(`✅ Demo · ${result.poll?.notifications || 0} notificación(es)`);
        await load({ quiet: true });
      } catch (e) {
        showToast(e.message, "err");
      } finally {
        btn.disabled = false;
      }
    };
  });

  box.querySelectorAll("form.product-edit").forEach((form) => {
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      const recordId = form.dataset.record;
      const fd = new FormData(form);
      const body = {
        monthly_price: fd.get("monthly_price"),
        previous_monthly_price: fd.get("previous_monthly_price"),
        price: fd.get("price"),
        promotion: fd.get("promotion"),
        gift: fd.get("gift"),
        active: form.querySelector('[name="active"]').checked,
        featured: form.querySelector('[name="featured"]').checked,
        is_new: form.querySelector('[name="is_new"]').checked,
      };
      const submit = form.querySelector('[type="submit"]');
      submit.disabled = true;
      try {
        await api(`/api/movistar/admin/products/${recordId}`, { method: "PATCH", body: JSON.stringify(body) });
        showToast("✅ Guardado en NocoDB");
        await load({ quiet: true });
      } catch (e) {
        showToast(e.message, "err");
      } finally {
        submit.disabled = false;
      }
    };
  });
}

function renderBrands() {
  const brands = [...new Set(catalog.map((p) => p.brand).filter(Boolean))].sort();
  const sel = document.getElementById("brandFilter");
  const current = sel.value;
  sel.innerHTML = `<option value="">Todas las marcas</option>` +
    brands.map((b) => `<option value="${esc(b)}">${esc(b)}</option>`).join("");
  sel.value = current;
}

function renderAlerts(alerts) {
  const box = document.getElementById("alertsTable");
  if (!alerts.length) {
    box.innerHTML = `<div class="empty">No hay avisos activos.</div>`;
    return;
  }
  const labels = {
    price_drop: "Si baja de precio",
    monthly_price_drop: "Si baja la cuota",
    better_deal: "Mejor oferta",
  };
  box.innerHTML = `<table class="data-table">
    <thead><tr><th>Usuario</th><th>Producto</th><th>Tipo</th><th>Objetivo</th><th>Creado</th></tr></thead>
    <tbody>${alerts.map((a) => `<tr>
      <td><code>${esc(a.telegram_user_id)}</code></td>
      <td>${esc(a.product_name || a.product_id)}</td>
      <td>${esc(labels[a.alert_type] || a.alert_type)}</td>
      <td>${a.target_monthly_price != null ? fmtMoney(a.target_monthly_price) : "—"}</td>
      <td>${esc((a.created_at || "").slice(0, 19).replace("T", " "))}</td>
    </tr>`).join("")}</tbody></table>`;
}

function renderEvents(events) {
  const box = document.getElementById("eventsTable");
  if (!events.length) {
    box.innerHTML = `<div class="empty">Sin eventos recientes.</div>`;
    return;
  }
  box.innerHTML = `<table class="data-table">
    <thead><tr><th>Tipo</th><th>Producto</th><th>Antes</th><th>Ahora</th><th>Fecha</th></tr></thead>
    <tbody>${events.map((e) => `<tr>
      <td><code>${esc(e.event_type)}</code></td>
      <td>${esc(e.product_id || "—")}</td>
      <td>${esc(e.old_value || "—")}</td>
      <td>${esc(e.new_value || "—")}</td>
      <td>${esc((e.created_at || "").slice(0, 19).replace("T", " "))}</td>
    </tr>`).join("")}</tbody></table>`;
}

function renderDemoQuick() {
  const heroes = ["pixel-11-256", "galaxy-s25", "iphone-16-128"];
  const box = document.getElementById("demoQuickActions");
  const picks = catalog.filter((p) => heroes.includes(p.id));
  box.innerHTML = picks.map((p) => {
    const action = (p.demo_actions || [])[0];
    if (!action) return "";
    return `<button class="action-btn sim-btn" data-id="${esc(p.id)}" data-price="${action.new_monthly}">
      Demo: ${esc(p.display_name)} → ${action.new_monthly} €/mes
    </button>`;
  }).join("");
  box.querySelectorAll(".sim-btn").forEach((btn) => {
    btn.onclick = async () => {
      try {
        const result = await api(`/api/movistar/admin/simulate-drop/${btn.dataset.id}?new_monthly=${btn.dataset.price}`, { method: "POST" });
        showToast(`Demo ejecutada · ${result.poll?.notifications || 0} notificación(es)`);
        await load({ quiet: true });
      } catch (e) {
        showToast(e.message, "err");
      }
    };
  });
}

async function load(opts = {}) {
  try {
    [dashboard, catalog] = await Promise.all([
      api("/api/movistar/admin/dashboard"),
      api("/api/movistar/admin/catalog"),
    ]);
    const alerts = await api("/api/movistar/admin/alerts");
    activeAlerts = alerts;
    const events = await api("/api/movistar/admin/events?limit=30");
    setConnected(true);
    renderStats();
    renderBrands();
    renderCatalog();
    renderAlerts(alerts);
    renderEvents(events);
    renderDemoQuick();
    document.getElementById("lastRefresh").textContent = `Sincronizado: ${new Date().toLocaleTimeString("es-ES")} · ${catalog.length} productos`;
    if (!opts.quiet) showToast(`Catálogo cargado · ${catalog.length} productos desde NocoDB`);
  } catch (e) {
    setConnected(false);
    document.getElementById("catalogTable").innerHTML = `
      <div class="empty"><strong>No se pudo conectar</strong><br>${esc(e.message)}<br><br>Recarga la página (<code>/panel</code>).</div>`;
    if (!opts.quiet) showToast(`Error: ${e.message}`, "err");
  }
}

["searchInput", "brandFilter", "activeOnly", "alertsOnly"].forEach((id) => {
  document.getElementById(id).addEventListener("input", renderCatalog);
  document.getElementById(id).addEventListener("change", renderCatalog);
});

load();
