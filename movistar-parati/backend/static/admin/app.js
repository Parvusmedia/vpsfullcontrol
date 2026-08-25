const keyInput = document.getElementById("adminKey");
const toastEl = document.getElementById("toast");
let catalog = [];
let dashboard = null;

const saved = localStorage.getItem("mp_admin_key");
if (saved) keyInput.value = saved;

function headers() {
  return { "X-Admin-Key": keyInput.value, "Content-Type": "application/json" };
}

function showToast(message, type = "ok") {
  toastEl.textContent = message;
  toastEl.className = `toast ${type}`;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.add("hidden"), 5000);
}

function fmtMoney(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${Number(v).toFixed(2)} €/mes`;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function api(path, options = {}) {
  const res = await fetch(path, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

function setConnected(ok) {
  const pill = document.getElementById("connStatus");
  pill.textContent = ok ? "Conectado" : "Sin conectar";
  pill.classList.toggle("ok", ok);
}

function switchView(name) {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
}

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.onclick = () => switchView(btn.dataset.view);
});

document.getElementById("saveKey").onclick = () => {
  localStorage.setItem("mp_admin_key", keyInput.value);
  load();
};

document.getElementById("pollNow").onclick = async () => {
  try {
    const result = await api("/api/movistar/admin/poll", { method: "POST" });
    showToast(`Detección OK · ${result.changes} cambios · ${result.notifications} notificaciones`);
    await load();
  } catch (e) {
    showToast(e.message, "err");
  }
};

function renderStats() {
  if (!dashboard) return;
  document.getElementById("stats").innerHTML = `
    <div class="metric"><span>Productos activos</span><strong>${dashboard.products_active}</strong></div>
    <div class="metric"><span>En catálogo total</span><strong>${dashboard.products_total}</strong></div>
    <div class="metric"><span>Ofertas destacadas</span><strong>${dashboard.featured}</strong></div>
    <div class="metric"><span>Novedades</span><strong>${dashboard.new_products}</strong></div>
    <div class="metric"><span>Avisos activos</span><strong>${dashboard.alerts_active}</strong></div>
  `;
  document.getElementById("nocodbLink").href = dashboard.nocodb_products_url;
}

function filteredCatalog() {
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  const brand = document.getElementById("brandFilter").value;
  const activeOnly = document.getElementById("activeOnly").checked;
  return catalog.filter((p) => {
    if (activeOnly && !p.active) return false;
    if (brand && p.brand !== brand) return false;
    if (!q) return true;
    const hay = `${p.id} ${p.brand} ${p.name} ${p.display_name}`.toLowerCase();
    return hay.includes(q);
  });
}

function renderCatalog() {
  const items = filteredCatalog();
  const box = document.getElementById("catalogTable");
  if (!items.length) {
    box.innerHTML = `<div class="empty">No hay productos que coincidan con el filtro.</div>`;
    return;
  }
  box.innerHTML = items.map((p) => {
    const badges = [
      p.active ? "" : `<span class="badge inactive">Inactivo</span>`,
      p.featured ? `<span class="badge featured">Destacado</span>` : "",
      p.is_new ? `<span class="badge new">Nuevo</span>` : "",
      `<span class="badge">${esc(p.brand)}</span>`,
    ].join("");
    const actions = (p.demo_actions || []).map((a) =>
      `<button class="action-btn" data-id="${esc(p.id)}" data-price="${a.new_monthly}">${esc(a.label)}</button>`
    ).join("");
    const prev = p.previous_monthly_price && p.previous_monthly_price > p.monthly_price
      ? `<div class="prev">${fmtMoney(p.previous_monthly_price)}</div>` : "";
    return `
      <article class="product-row ${p.active ? "" : "inactive"}" data-id="${esc(p.id)}">
        <img class="thumb" src="${esc(p.image_api_url)}" alt="${esc(p.display_name)}" loading="lazy" />
        <div class="product-main">
          <strong>${esc(p.display_name)}</strong>
          <div class="product-meta">ID: <code>${esc(p.id)}</code> · ${esc(p.category || "smartphone")}</div>
          <div class="badges">${badges}</div>
        </div>
        <div class="price-block">
          <div class="current">${fmtMoney(p.monthly_price)}</div>
          ${prev}
          <div class="product-meta">${p.price ? `${Number(p.price).toFixed(0)} € total` : ""}</div>
        </div>
        <div class="actions">${actions || `<span class="product-meta">Sin acciones demo</span>`}</div>
      </article>`;
  }).join("");

  box.querySelectorAll(".action-btn").forEach((btn) => {
    btn.onclick = async () => {
      btn.disabled = true;
      try {
        const id = btn.dataset.id;
        const price = btn.dataset.price;
        const result = await api(`/api/movistar/admin/simulate-drop/${id}?new_monthly=${price}`, { method: "POST" });
        const poll = result.poll || {};
        showToast(`✅ ${id} → ${price} €/mes · ${poll.notifications || 0} notificación(es)`);
        await load();
      } catch (e) {
        showToast(e.message, "err");
      } finally {
        btn.disabled = false;
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
    return `<button class="action-btn" data-id="${esc(p.id)}" data-price="${action.new_monthly}">
      Demo: ${esc(p.display_name)} → ${action.new_monthly} €/mes
    </button>`;
  }).join("");
  box.querySelectorAll(".action-btn").forEach((btn) => {
    btn.onclick = async () => {
      try {
        const result = await api(`/api/movistar/admin/simulate-drop/${btn.dataset.id}?new_monthly=${btn.dataset.price}`, { method: "POST" });
        showToast(`Demo ejecutada · ${result.poll?.notifications || 0} notificación(es)`);
        await load();
      } catch (e) {
        showToast(e.message, "err");
      }
    };
  });
}

async function load() {
  if (!keyInput.value) {
    setConnected(false);
    return;
  }
  try {
    [dashboard, catalog] = await Promise.all([
      api("/api/movistar/admin/dashboard"),
      api("/api/movistar/admin/catalog"),
    ]);
    const alerts = await api("/api/movistar/admin/alerts");
    const events = await api("/api/movistar/admin/events?limit=30");
    setConnected(true);
    renderStats();
    renderBrands();
    renderCatalog();
    renderAlerts(alerts);
    renderEvents(events);
    renderDemoQuick();
    document.getElementById("lastRefresh").textContent = `Actualizado: ${new Date().toLocaleTimeString("es-ES")}`;
  } catch (e) {
    setConnected(false);
    showToast(`Error de conexión: ${e.message}`, "err");
  }
}

["searchInput", "brandFilter", "activeOnly"].forEach((id) => {
  document.getElementById(id).addEventListener("input", renderCatalog);
  document.getElementById(id).addEventListener("change", renderCatalog);
});

load();
