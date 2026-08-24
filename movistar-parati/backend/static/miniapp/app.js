const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const tabs = [
  { id: "all", label: "Para ti" },
  { id: "smartphone", label: "Móviles" },
  { id: "tv", label: "TV" },
  { id: "gaming", label: "Gaming" },
  { id: "computing", label: "Informática" },
];

let activeTab = "all";

function headers() {
  const h = { "Content-Type": "application/json" };
  if (tg?.initDataUnsafe?.user?.id) {
    h["X-Telegram-User-Id"] = String(tg.initDataUnsafe.user.id);
  }
  return h;
}

async function loadProducts() {
  const url = activeTab === "all" ? "/api/products" : `/api/products?category=${activeTab}`;
  const res = await fetch(url, { headers: headers() });
  const products = await res.json();
  renderProducts(products);
  if (tg?.initDataUnsafe?.user?.id) {
    fetch("/api/miniapp/me", { headers: headers() });
  }
}

function renderTabs() {
  const nav = document.getElementById("tabs");
  nav.innerHTML = tabs
    .map(
      (t) =>
        `<button class="${t.id === activeTab ? "active" : ""}" data-tab="${t.id}">${t.label}</button>`
    )
    .join("");
  nav.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeTab = btn.dataset.tab;
      renderTabs();
      loadProducts();
    });
  });
}

function renderProducts(products) {
  const main = document.getElementById("products");
  if (!products.length) {
    main.innerHTML = "<p>No hay productos en esta categoría.</p>";
    return;
  }
  main.innerHTML = products
    .map(
      (p) => `
    <article class="card">
      <img src="${p.image_url || ""}" alt="${p.name}" />
      <div class="card-body">
        <div class="brand">${p.brand}</div>
        <div class="name">${p.name}</div>
        <div class="price-old">ANTES ${p.original_monthly_price.toFixed(2)} €/mes</div>
        <div class="price-now">AHORA ${p.monthly_price.toFixed(2)} €/mes</div>
        ${p.promotion_label ? `<span class="badge">🔥 ${p.promotion_label}</span>` : ""}
        <div class="actions">
          <a class="btn-primary" href="${p.purchase_url}" target="_blank">Ver oferta</a>
          <button class="btn-secondary" data-follow="${p.id}">🔔 Seguir</button>
        </div>
      </div>
    </article>`
    )
    .join("");

  main.querySelectorAll("[data-follow]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!tg?.initDataUnsafe?.user?.id) {
        alert("Abre la Mini App desde Telegram para seguir productos.");
        return;
      }
      await fetch(`/api/products/${btn.dataset.follow}/follow?telegram_user_id=${tg.initDataUnsafe.user.id}`, {
        method: "POST",
        headers: headers(),
      });
      btn.textContent = "✓ Siguiendo";
    });
  });
}

renderTabs();
loadProducts();
