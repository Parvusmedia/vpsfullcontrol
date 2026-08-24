const keyInput = document.getElementById("adminKey");
const saved = localStorage.getItem("mp_admin_key");
if (saved) keyInput.value = saved;

document.getElementById("saveKey").onclick = () => {
  localStorage.setItem("mp_admin_key", keyInput.value);
  load();
};

function headers() {
  return { "X-Admin-Key": keyInput.value, "Content-Type": "application/json" };
}

async function load() {
  const products = await (await fetch("/api/movistar/products", { headers: headers() })).json();
  document.getElementById("stats").innerHTML = `
    <div class="metric"><span>Productos</span><strong>${products.length}</strong></div>
    <div class="metric"><span>Ofertas destacadas</span><strong>${products.filter(p => p.featured).length}</strong></div>
    <div class="metric"><span>Novedades</span><strong>${products.filter(p => p.is_new).length}</strong></div>
  `;
  const box = document.getElementById("products");
  box.innerHTML = products.map(p => `
    <div class="card">
      <strong>${p.name} ${p.capacity || ""}</strong>
      <div>${p.monthly_price?.toFixed(2)} €/mes · ${p.brand}</div>
      <div class="actions">
        <button data-id="${p.id}" data-price="${p.monthly_price}" class="sim">Simular bajada → 11.99</button>
      </div>
    </div>
  `).join("");
  box.querySelectorAll(".sim").forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.id;
      const res = await fetch(`/api/movistar/admin/simulate-drop/${id}?new_monthly=11.99`, { method: "POST", headers: headers() });
      alert(JSON.stringify(await res.json(), null, 2));
      load();
    };
  });
}

document.getElementById("pollNow").onclick = async () => {
  const res = await fetch("/api/movistar/admin/poll", { method: "POST", headers: headers() });
  alert(JSON.stringify(await res.json(), null, 2));
};

load();
