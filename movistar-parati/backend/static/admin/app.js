const keyInput = document.getElementById("adminKey");
const saved = localStorage.getItem("mp_admin_key");
if (saved) keyInput.value = saved;

document.getElementById("saveKey").onclick = () => {
  localStorage.setItem("mp_admin_key", keyInput.value);
  loadDashboard();
};

function adminHeaders() {
  return { "X-Admin-Key": keyInput.value, "Content-Type": "application/json" };
}

async function loadDashboard() {
  const res = await fetch("/api/admin/dashboard", { headers: adminHeaders() });
  if (!res.ok) return;
  const data = await res.json();
  const el = document.getElementById("dashboard");
  el.innerHTML = `
    <div class="metric"><span>Usuarios</span><strong>${data.users}</strong></div>
    <div class="metric"><span>Alertas activas</span><strong>${data.active_alerts}</strong></div>
    <div class="metric"><span>Black Friday</span><strong>${data.black_friday_registered}</strong></div>
    <div class="metric"><span>Preventas</span><strong>${data.preorder_registered}</strong></div>
  `;
  const pixel = (await (await fetch("/api/products/pixel-11")).json());
  document.getElementById("pixelPrice").textContent = `${pixel.monthly_price.toFixed(2)} €/mes`;
}

async function post(url, body = {}) {
  const res = await fetch(url, { method: "POST", headers: adminHeaders(), body: JSON.stringify(body) });
  return res.json();
}

document.getElementById("dropPixel").onclick = async () => {
  const out = await post("/api/admin/products/pixel-11/price", { monthly_price: 8.5, original_monthly_price: 12 });
  document.getElementById("pixelResult").textContent = JSON.stringify(out, null, 2);
  loadDashboard();
};

document.getElementById("openPreorder").onclick = async () => {
  const out = await post("/api/admin/preorders/iphone-next/open");
  document.getElementById("preorderResult").textContent = JSON.stringify(out, null, 2);
};

document.getElementById("activateBf").onclick = async () => {
  const out = await post("/api/admin/campaigns/black-friday-2026/activate");
  document.getElementById("bfResult").textContent = JSON.stringify(out, null, 2);
};

loadDashboard();
