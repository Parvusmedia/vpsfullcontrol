const CATALOG = {
  color: {
    title: "Hs color",
    items: [
      { id: "booster-violeta", name: "Booster violeta" },
      { id: "booster-red", name: "Booster red" },
      { id: "booster-copper", name: "Booster copper" },
      { id: "6-00", name: "6.00" },
      { id: "7-00", name: "7.00" },
      { id: "8-00", name: "8.00" },
      { id: "9-00", name: "9.00" },
      { id: "9-13", name: "9.13" },
      { id: "7-11", name: "7.11" },
      { id: "9-11", name: "9.11" },
      { id: "7-34", name: "7.34" },
      { id: "8-34", name: "8.34" },
      { id: "10-1", name: "10.1" },
      { id: "11-1", name: "11.1" },
      { id: "8-11", name: "8.11" },
    ],
  },
  oxigenada: {
    title: "Oxigenada Every Green",
    items: [
      { id: "ox-5", name: "5 vol.", meta: "Oxigenada Every Green" },
      { id: "ox-10", name: "10 vol.", meta: "Oxigenada Every Green" },
      { id: "ox-20", name: "20 vol.", meta: "Oxigenada Every Green" },
    ],
  },
  decoloracion: {
    title: "Decoloración",
    items: [{ id: "deco-10t", name: "Deco 10 T", meta: "Polvo decolorante" }],
  },
  cuidado: {
    title: "Cuidado",
    items: [
      { id: "ch-kera-350", name: "Champú Kera", meta: "350 ml" },
      { id: "mask-kera-500", name: "Mascarilla Kera", meta: "500 ml" },
      { id: "ch-yellow-350", name: "Champú Yellow", meta: "350 ml" },
      { id: "serum-95", name: "Serum Iluminador", meta: "nº 95" },
    ],
  },
};

/** @type {Record<string, number>} */
const quantities = {};

function initQuantities() {
  for (const cat of Object.values(CATALOG)) {
    for (const item of cat.items) {
      quantities[item.id] = 0;
    }
  }
}

function renderProductList(categoryKey, containerId) {
  const container = document.getElementById(containerId);
  const cat = CATALOG[categoryKey];
  container.innerHTML = "";

  for (const item of cat.items) {
    const row = document.createElement("div");
    row.className = "product-row";
    row.dataset.id = item.id;

    const info = document.createElement("div");
    info.innerHTML = `
      <div class="product-row__name">${escapeHtml(item.name)}</div>
      ${item.meta ? `<div class="product-row__meta">${escapeHtml(item.meta)}</div>` : ""}
    `;

    const control = document.createElement("div");
    control.className = "qty-control";
    control.innerHTML = `
      <button type="button" aria-label="Menos" data-action="dec">−</button>
      <input type="number" min="0" step="1" value="0" inputmode="numeric" aria-label="Cantidad ${escapeHtml(item.name)}" />
      <button type="button" aria-label="Más" data-action="inc">+</button>
    `;

    const input = control.querySelector("input");
    input.addEventListener("change", () => setQty(item.id, input.value));
    input.addEventListener("input", () => setQty(item.id, input.value, { soft: true }));

    control.querySelector('[data-action="dec"]').addEventListener("click", () => {
      setQty(item.id, Math.max(0, (quantities[item.id] || 0) - 1));
      syncInput(input, item.id);
    });
    control.querySelector('[data-action="inc"]').addEventListener("click", () => {
      setQty(item.id, (quantities[item.id] || 0) + 1);
      syncInput(input, item.id);
    });

    row.append(info, control);
    container.appendChild(row);
  }
}

function syncInput(input, id) {
  input.value = String(quantities[id] || 0);
}

function setQty(id, raw, opts = {}) {
  let n = parseInt(String(raw), 10);
  if (Number.isNaN(n) || n < 0) n = 0;
  quantities[id] = n;
  if (!opts.soft) updateCart();
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function findItem(id) {
  for (const [catKey, cat] of Object.entries(CATALOG)) {
    const item = cat.items.find((i) => i.id === id);
    if (item) return { ...item, categoryKey: catKey, categoryTitle: cat.title };
  }
  return null;
}

function getOrderLines() {
  const lines = [];
  for (const [id, qty] of Object.entries(quantities)) {
    if (qty > 0) {
      const item = findItem(id);
      if (item) lines.push({ ...item, qty });
    }
  }
  return lines;
}

function formatOrderText() {
  const salon = document.getElementById("salon-name").value.trim();
  const lines = getOrderLines();
  const parts = ["HS Pedido:"];
  if (salon) parts.push(`Cliente: ${salon}`);
  parts.push("");

  const byCat = {};
  for (const line of lines) {
    if (!byCat[line.categoryKey]) byCat[line.categoryKey] = [];
    byCat[line.categoryKey].push(line);
  }

  for (const [catKey, catLines] of Object.entries(byCat)) {
    parts.push(CATALOG[catKey].title + ":");
    for (const line of catLines) {
      if (catKey === "color") {
        parts.push(`${line.name}/${line.qty}`);
      } else if (catKey === "oxigenada") {
        parts.push(`${line.qty} uds de ${line.name.replace(".", "")}`);
      } else {
        parts.push(`${line.qty} uds ${line.name}${line.meta ? " " + line.meta : ""}`);
      }
    }
    parts.push("");
  }

  return parts.join("\n").trim();
}

function updateCart() {
  const lines = getOrderLines();
  const listEl = document.getElementById("cart-lines");
  const emptyEl = document.getElementById("cart-empty");
  const countEl = document.getElementById("cart-count");
  const btnCopy = document.getElementById("btn-copy");
  const btnSubmit = document.getElementById("btn-submit");

  listEl.innerHTML = "";
  for (const line of lines) {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(line.name)}</span><span class="qty">${line.qty} uds</span>`;
    listEl.appendChild(li);
  }

  const hasItems = lines.length > 0;
  emptyEl.hidden = hasItems;
  countEl.textContent = hasItems ? `${lines.length} línea${lines.length === 1 ? "" : "s"}` : "0 líneas";
  btnCopy.disabled = !hasItems;
  btnSubmit.disabled = !hasItems;

  document.querySelectorAll(".product-row input").forEach((input) => {
    const row = input.closest(".product-row");
    if (row) syncInput(input, row.dataset.id);
  });
}

function showToast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => {
    el.hidden = true;
  }, 2600);
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tabs__btn");
  const panels = {
    color: document.getElementById("panel-color"),
    oxigenada: document.getElementById("panel-oxigenada"),
    decoloracion: document.getElementById("panel-decoloracion"),
    cuidado: document.getElementById("panel-cuidado"),
  };

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      buttons.forEach((b) => {
        b.classList.toggle("is-active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      });
      Object.entries(panels).forEach(([key, panel]) => {
        const visible = key === tab;
        panel.classList.toggle("is-visible", visible);
        panel.hidden = !visible;
      });
    });
  });
}

function setupActions() {
  document.getElementById("btn-copy").addEventListener("click", async () => {
    const text = formatOrderText();
    try {
      await navigator.clipboard.writeText(text);
      showToast("Pedido copiado al portapapeles");
    } catch {
      showToast("No se pudo copiar — usa Enviar pedido");
    }
  });

  const modal = document.getElementById("modal-success");
  document.getElementById("btn-submit").addEventListener("click", () => {
    document.getElementById("modal-preview").textContent = formatOrderText();
    modal.showModal();
  });
  document.getElementById("modal-close").addEventListener("click", () => modal.close());
}

initQuantities();
renderProductList("color", "list-color");
renderProductList("oxigenada", "list-oxigenada");
renderProductList("decoloracion", "list-decoloracion");
renderProductList("cuidado", "list-cuidado");
setupTabs();
setupActions();
updateCart();
