const I18N = {
  en: {
    "nav.companies": "Companies",
    "nav.salesnav": "Sales Navigator",
    "hero.kicker": "Paste a Sales Navigator list or search URL.",
    "hero.title": "Export leads to CSV in minutes.",
    "hero.lede":
      "Turn saved SN lists and people searches into a clean CSV — name, job title, company, location and LinkedIn profile URL — ready for CRM or outreach.",
    "hero.note":
      "Connect your LinkedIn account with Sales Navigator, then paste a list or search URL. Demo exports up to <strong>25 leads</strong> free.",
    "connect.title": "LinkedIn connection",
    "connect.disconnected": "Not connected",
    "connect.connected": "Connected",
    "connect.connectedAs": "Connected as {label}",
    "connect.body":
      "Connect your LinkedIn / Sales Navigator seat securely via Unipile. We never store your password.",
    "connect.cta": "Connect LinkedIn",
    "connect.disconnect": "Disconnect",
    "connect.reconnect": "Reconnect",
    "connect.starting": "Opening secure connection…",
    "connect.success": "LinkedIn connected. You can export now.",
    "connect.failed": "Connection failed or was cancelled. Try again.",
    "connect.required": "Connect LinkedIn before exporting.",
    "credits.balance": "{count} export credits available",
    "credits.required": "Buy export credits first — 1 credit = 1 lead in your CSV.",
    "credits.buy": "Buy credits",
    "credits.checkoutOpened": "Stripe checkout opened in a new window. Return here after payment.",
    "credits.paid": "Credits added. You can connect LinkedIn now.",
    "credits.cancelled": "Payment cancelled.",
    "credits.insufficient": "Not enough credits for this export. Buy more credits.",
    "mode.list": "Lead list",
    "mode.search": "People search",
    "form.listLabel": "Sales Navigator list URL",
    "form.listPlaceholder": "https://www.linkedin.com/sales/lists/people/…",
    "form.searchLabel": "Sales Navigator search URL",
    "form.searchPlaceholder": "https://www.linkedin.com/sales/search/people?…",
    "form.limit": "Max leads",
    "form.limit25": "25 (demo)",
    "form.limit100": "100",
    "form.limit500": "500",
    "form.limit2000": "2,000 (max)",
    "form.submit": "Export CSV",
    "form.hint":
      "Open your list in Sales Navigator, copy the browser URL and paste it above. Large lists may take a minute — keep this tab open.",
    "progress.label": "Exporting leads…",
    "results.title": "Export ready",
    "results.another": "Export another",
    "results.csv": "Download CSV",
    "results.volume": "Request volume access",
    "results.summary": "Exported {count} leads in {seconds}s (showing first 10).",
    "col.name": "Name",
    "col.title": "Title",
    "col.company": "Company",
    "col.location": "Location",
    "tiers.title": "Modular tiers",
    "tiers.lede":
      "Start with Basic export pricing. Add Enriched or Mail only when you need those columns — same colors as the CSV preview above.",
    "tiers.basic.badge": "Basic",
    "tiers.basic.price": "€0.05",
    "tiers.basic.priceUnit": "/ lead",
    "tiers.basic.priceNote": "Base export · available now",
    "tiers.basic.title": "Basic",
    "tiers.basic.body":
      "Sales Navigator list/search export — name, title, company, location, LinkedIn URL and SN metadata.",
    "tiers.enriched.badge": "Enriched",
    "tiers.enriched.price": "+ €0.02",
    "tiers.enriched.priceUnit": "/ lead",
    "tiers.enriched.priceNote": "Add-on to Basic",
    "tiers.enriched.title": "Enriched",
    "tiers.enriched.body":
      "Company domain, industry, size, HQ, seniority, tenure, summary, skills and languages.",
    "tiers.mail.badge": "Mail",
    "tiers.mail.price": "+ €0.09",
    "tiers.mail.priceUnit": "/ email found",
    "tiers.mail.priceNote": "Add-on · pay only when found",
    "tiers.mail.title": "Mail",
    "tiers.mail.body":
      "Work email discovery with status, confidence and source — ideal for outbound teams.",
    "pricing.kicker": "Volume & API",
    "pricing.title": "Need higher limits or automation?",
    "pricing.lede":
      "Tell us your monthly lead volume and whether you need enrichment or email. We will send pricing and enable full exports on your workspace.",
    "pricing.b1": "Full list exports beyond the demo limit",
    "pricing.b2": "Optional company enrichment via CompanyDataEnrichment",
    "pricing.b3": "API access for CRM and workflow automation",
    "contact.title": "Request access",
    "contact.name": "Name",
    "contact.company": "Company",
    "contact.email": "Corporate email",
    "contact.volume": "Leads per month",
    "contact.volumePlaceholder": "Select volume…",
    "contact.volume500": "Up to 500",
    "contact.volume1k3k": "1,000 – 3,000",
    "contact.volume3k10k": "3,000 – 10,000",
    "contact.volume10k": "10,000+",
    "contact.tier": "Tier interest",
    "contact.tierBasic": "Basic export",
    "contact.tierEnriched": "Basic + Enriched",
    "contact.tierMail": "Basic + Enriched + Mail",
    "contact.captcha": "Anti-spam",
    "contact.submit": "Send request",
    "contact.privacy":
      'We will only use these details to reply about Sales Navigator export. <a href="/privacy.html">Privacy policy</a>.',
    "contact.okKicker": "Request sent",
    "contact.okTitle": "Thanks — we got your message.",
    "contact.okBody": "We will reply to your corporate email shortly.",
    "contact.again": "Send another request",
    "trust.title": "Usage & compliance",
    "trust.p1":
      "Exports use your LinkedIn Sales Navigator access via a secure integration — you must have rights to the list you export.",
    "trust.p2":
      "Output is assistive prospecting data. Review before CRM import or outreach; follow LinkedIn terms and applicable privacy rules.",
    "trust.p3":
      "Demo rate limits apply on this page. Volume customers get dedicated limits aligned with LinkedIn daily export caps (~2,000/day per SN seat).",
    "trust.privacy": "Terms & privacy policy",
    "footer.tag": "Company enrichment · Sales Navigator export",
    "footer.privacy": "Privacy",
    "msg.challenge": "Security check failed. Refresh the page and try again.",
    "msg.generic": "Something went wrong. Please try again.",
    "msg.rateLimit": "Rate limit reached. Try again later or request volume access.",
    "msg.empty": "No leads returned. Check the URL and Sales Navigator access.",
    "msg.exporting": "Exporting… this may take up to a minute for large lists.",
    "msg.contactOk": "Request sent. We will reply by email.",
  },
  es: {
    "nav.companies": "Empresas",
    "nav.salesnav": "Sales Navigator",
    "hero.kicker": "Pega la URL de una lista o búsqueda de Sales Navigator.",
    "hero.title": "Exporta leads a CSV en minutos.",
    "hero.lede":
      "Convierte listas guardadas y búsquedas de SN en un CSV limpio — nombre, cargo, empresa, ubicación y URL de LinkedIn — listo para CRM o outreach.",
    "hero.note":
      "Conecta tu cuenta LinkedIn con Sales Navigator y pega la URL de lista o búsqueda. Demo gratis hasta <strong>25 leads</strong>.",
    "connect.title": "Conexión LinkedIn",
    "connect.disconnected": "Sin conectar",
    "connect.connected": "Conectado",
    "connect.connectedAs": "Conectado como {label}",
    "connect.body":
      "Conecta tu seat de LinkedIn / Sales Navigator de forma segura vía Unipile. No guardamos tu contraseña.",
    "connect.cta": "Conectar LinkedIn",
    "connect.disconnect": "Desconectar",
    "connect.reconnect": "Reconectar",
    "connect.starting": "Abriendo conexión segura…",
    "connect.success": "LinkedIn conectado. Ya puedes exportar.",
    "connect.failed": "Conexión fallida o cancelada. Inténtalo de nuevo.",
    "connect.required": "Conecta LinkedIn antes de exportar.",
    "credits.balance": "{count} créditos de export disponibles",
    "credits.required": "Compra créditos primero — 1 crédito = 1 lead en tu CSV.",
    "credits.buy": "Comprar créditos",
    "credits.checkoutOpened": "Checkout de Stripe abierto en ventana nueva. Vuelve aquí tras pagar.",
    "credits.paid": "Créditos añadidos. Ya puedes conectar LinkedIn.",
    "credits.cancelled": "Pago cancelado.",
    "credits.insufficient": "Créditos insuficientes para este export. Compra más créditos.",
    "mode.list": "Lista de leads",
    "mode.search": "Búsqueda de personas",
    "form.listLabel": "URL de lista Sales Navigator",
    "form.listPlaceholder": "https://www.linkedin.com/sales/lists/people/…",
    "form.searchLabel": "URL de búsqueda Sales Navigator",
    "form.searchPlaceholder": "https://www.linkedin.com/sales/search/people?…",
    "form.limit": "Máx. leads",
    "form.limit25": "25 (demo)",
    "form.limit100": "100",
    "form.limit500": "500",
    "form.limit2000": "2.000 (máx.)",
    "form.submit": "Exportar CSV",
    "form.hint":
      "Abre tu lista en Sales Navigator, copia la URL del navegador y pégala arriba. Listas grandes pueden tardar un minuto — no cierres esta pestaña.",
    "progress.label": "Exportando leads…",
    "results.title": "Exportación lista",
    "results.another": "Exportar otra",
    "results.csv": "Descargar CSV",
    "results.volume": "Pedir acceso por volumen",
    "results.summary": "Exportados {count} leads en {seconds}s (mostrando los 10 primeros).",
    "col.name": "Nombre",
    "col.title": "Cargo",
    "col.company": "Empresa",
    "col.location": "Ubicación",
    "tiers.title": "Tiers modulares",
    "tiers.lede":
      "Empieza con el precio Basic. Añade Enriched o Mail solo si necesitas esas columnas — mismos colores que el preview CSV de arriba.",
    "tiers.basic.badge": "Basic",
    "tiers.basic.price": "€0,05",
    "tiers.basic.priceUnit": "/ lead",
    "tiers.basic.priceNote": "Export base · disponible ya",
    "tiers.basic.title": "Basic",
    "tiers.basic.body":
      "Export de lista/búsqueda SN — nombre, cargo, empresa, ubicación, URL LinkedIn y metadatos SN.",
    "tiers.enriched.badge": "Enriched",
    "tiers.enriched.price": "+ €0,02",
    "tiers.enriched.priceUnit": "/ lead",
    "tiers.enriched.priceNote": "Extra sobre Basic",
    "tiers.enriched.title": "Enriched",
    "tiers.enriched.body":
      "Dominio, industria, tamaño, HQ, seniority, antigüedad, resumen, skills e idiomas.",
    "tiers.mail.badge": "Mail",
    "tiers.mail.price": "+ €0,09",
    "tiers.mail.priceUnit": "/ email encontrado",
    "tiers.mail.priceNote": "Extra · pagas solo si se encuentra",
    "tiers.mail.title": "Mail",
    "tiers.mail.body":
      "Email laboral con status, confianza y fuente — ideal para equipos de outbound.",
    "pricing.kicker": "Volumen y API",
    "pricing.title": "¿Necesitas más límite o automatización?",
    "pricing.lede":
      "Cuéntanos tu volumen mensual de leads y si necesitas enriquecimiento o email. Te enviamos pricing y activamos exports completos.",
    "pricing.b1": "Export de listas completas más allá del demo",
    "pricing.b2": "Enriquecimiento de empresa opcional vía CompanyDataEnrichment",
    "pricing.b3": "Acceso API para CRM y automatización",
    "contact.title": "Pedir acceso",
    "contact.name": "Nombre",
    "contact.company": "Empresa",
    "contact.email": "Email corporativo",
    "contact.volume": "Leads al mes",
    "contact.volumePlaceholder": "Selecciona volumen…",
    "contact.volume500": "Hasta 500",
    "contact.volume1k3k": "1.000 – 3.000",
    "contact.volume3k10k": "3.000 – 10.000",
    "contact.volume10k": "10.000+",
    "contact.tier": "Tier de interés",
    "contact.tierBasic": "Export Basic",
    "contact.tierEnriched": "Basic + Enriched",
    "contact.tierMail": "Basic + Enriched + Mail",
    "contact.captcha": "Anti-spam",
    "contact.submit": "Enviar solicitud",
    "contact.privacy":
      'Solo usaremos estos datos para responder sobre export Sales Navigator. <a href="/privacy.html">Política de privacidad</a>.',
    "contact.okKicker": "Solicitud enviada",
    "contact.okTitle": "Gracias — hemos recibido tu mensaje.",
    "contact.okBody": "Responderemos a tu email corporativo en breve.",
    "contact.again": "Enviar otra solicitud",
    "trust.title": "Uso y cumplimiento",
    "trust.p1":
      "Los exports usan tu acceso a Sales Navigator vía integración segura — debes tener derecho sobre la lista que exportas.",
    "trust.p2":
      "Los datos son auxiliares para prospección. Revísalos antes de importar al CRM o contactar; respeta los términos de LinkedIn y la normativa de privacidad.",
    "trust.p3":
      "Hay límites de demo en esta página. Clientes de volumen reciben límites dedicados (~2.000/día por seat SN).",
    "trust.privacy": "Términos y privacidad",
    "footer.tag": "Enriquecimiento de empresas · Export Sales Navigator",
    "footer.privacy": "Privacidad",
    "msg.challenge": "Falló la comprobación de seguridad. Recarga la página.",
    "msg.generic": "Algo salió mal. Inténtalo de nuevo.",
    "msg.rateLimit": "Límite de uso alcanzado. Prueba más tarde o pide acceso por volumen.",
    "msg.empty": "No se devolvieron leads. Revisa la URL y el acceso a Sales Navigator.",
    "msg.exporting": "Exportando… puede tardar hasta un minuto en listas grandes.",
    "msg.contactOk": "Solicitud enviada. Responderemos por email.",
  },
};

let lang = "en";
let lastRows = [];
let contactChallengeToken = "";
let isConnected = false;
let lastConnection = { connected: false, label: "" };
let billingEnabled = false;
let creditBalance = 0;

function t(key, vars = {}) {
  const str = I18N[lang][key] ?? I18N.en[key] ?? key;
  return str.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));
}

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    el.innerHTML = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key) el.placeholder = t(key);
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const active = btn.dataset.lang === lang;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function initLang() {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("lang");
  if (q === "es" || q === "en") lang = q;
  else if (navigator.language?.toLowerCase().startsWith("es")) lang = "es";
  applyI18n();
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      lang = btn.dataset.lang === "es" ? "es" : "en";
      applyI18n();
      renderConnectionStatus(lastConnection);
    });
  });
}

function setNote(text, tone = "ok") {
  const note = document.getElementById("form-note");
  if (!note) return;
  note.hidden = !text;
  note.dataset.tone = tone;
  note.textContent = text || "";
}

function setExportGate(visible) {
  const gate = document.getElementById("export-gate");
  if (gate) gate.hidden = !visible;
}

function renderConnectionStatus(data) {
  lastConnection = {
    connected: !!data?.connected,
    label: data?.label || "",
    connected_at: data?.connected_at || "",
  };
  isConnected = lastConnection.connected;
  const badge = document.getElementById("connect-badge");
  const copy = document.getElementById("connect-copy");
  const connectBtn = document.getElementById("connect-btn");
  const disconnectBtn = document.getElementById("disconnect-btn");
  const reconnectBtn = document.getElementById("reconnect-btn");

  if (badge) {
    badge.dataset.state = isConnected ? "connected" : "disconnected";
    if (isConnected && data.label) {
      badge.textContent = t("connect.connectedAs", { label: data.label });
    } else {
      badge.textContent = t(isConnected ? "connect.connected" : "connect.disconnected");
    }
  }

  if (copy && isConnected && data.label) {
    copy.textContent = t("connect.connectedAs", { label: data.label });
  } else if (copy) {
    copy.innerHTML = t("connect.body");
  }

  if (connectBtn) connectBtn.hidden = isConnected;
  if (disconnectBtn) disconnectBtn.hidden = !isConnected;
  if (reconnectBtn) reconnectBtn.hidden = !isConnected;

  setExportGate(isConnected);
  renderCredits();
}

function renderCredits() {
  const el = document.getElementById("connect-credits");
  const buyBtn = document.getElementById("buy-credits-btn");
  if (!el) return;
  if (!billingEnabled) {
    el.hidden = true;
    if (buyBtn) buyBtn.hidden = true;
    return;
  }
  el.hidden = false;
  el.textContent = t("credits.balance", { count: creditBalance });
  if (buyBtn) buyBtn.hidden = creditBalance > 0;
}

async function fetchCredits() {
  try {
    const res = await fetch("/api/salesnav-credits.php", { credentials: "same-origin" });
    const data = await res.json();
    if (!res.ok || !data.ok) return;
    billingEnabled = !!data.billing_enabled;
    creditBalance = Number(data.balance) || 0;
    renderCredits();
  } catch {
    /* optional */
  }
}

function openAuthPopup(url, messageType) {
  const features = "width=520,height=720,menubar=no,toolbar=no,location=yes,status=no,resizable=yes,scrollbars=yes";
  const popup = window.open(url, "salesnav_auth", features);
  if (!popup) {
    window.location.href = url;
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      window.removeEventListener("message", onMessage);
      clearInterval(timer);
      resolve(value);
    };
    const onMessage = (ev) => {
      if (ev.origin !== window.location.origin) return;
      if (ev.data?.type !== messageType) return;
      finish(!!ev.data.ok);
    };
    window.addEventListener("message", onMessage);
    const timer = setInterval(() => {
      if (popup.closed) finish(null);
    }, 500);
  });
}

async function startStripeCheckout(pack = "100") {
  const res = await fetch("/api/salesnav-stripe-checkout.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pack }),
  });
  const data = await res.json();
  if (!res.ok || !data.ok || !data.url) {
    throw new Error(data.error || t("msg.generic"));
  }
  window.open(data.url, "salesnav_stripe", "width=520,height=720,menubar=no,toolbar=no,location=yes,status=no");
  setNote(t("credits.checkoutOpened"), "ok");
}

async function fetchConnectionStatus() {
  const res = await fetch("/api/salesnav-status.php", { credentials: "same-origin" });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  renderConnectionStatus(data);
  return data;
}

async function pollConnectionStatus(attempts = 8, delayMs = 1500) {
  for (let i = 0; i < attempts; i += 1) {
    try {
      const data = await fetchConnectionStatus();
      if (data.connected) return data;
    } catch {
      /* retry */
    }
    await new Promise((r) => setTimeout(r, delayMs));
  }
  return { connected: false };
}

async function startConnect(reconnect = false) {
  const btn = document.getElementById("connect-btn");
  const reconnectBtn = document.getElementById("reconnect-btn");
  const active = reconnect ? reconnectBtn : btn;
  if (active) active.disabled = true;
  setNote(t("connect.starting"), "ok");
  try {
    if (!reconnect && billingEnabled && creditBalance <= 0) {
      setNote(t("credits.required"), "ok");
      await startStripeCheckout("100");
      return;
    }
    const res = await fetch("/api/salesnav-connect.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reconnect }),
    });
    const data = await res.json();
    if (res.status === 402 && data.needs_payment) {
      await startStripeCheckout("100");
      return;
    }
    if (!res.ok || !data.ok || !data.url) {
      throw new Error(data.error || t("msg.generic"));
    }
    const popupOk = await openAuthPopup(data.url, "salesnav-connect");
    const status = await pollConnectionStatus(12, 1500);
    if (status.connected) {
      setNote(t("connect.success"), "ok");
    } else if (popupOk === false) {
      setNote(t("connect.failed"), "error");
    } else if (popupOk === null && !status.connected) {
      setNote(t("connect.failed"), "error");
    }
  } catch (err) {
    setNote(err.message || t("msg.generic"), "error");
  } finally {
    if (active) active.disabled = false;
  }
}

async function disconnectLinkedIn() {
  try {
    const res = await fetch("/api/salesnav-disconnect.php", {
      method: "POST",
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || t("msg.generic"));
    }
    renderConnectionStatus({ connected: false });
    setNote("", "ok");
  } catch (err) {
    setNote(err.message || t("msg.generic"), "error");
  }
}

function handleConnectQuery() {
  const params = new URLSearchParams(window.location.search);
  const connected = params.get("connected");
  if (connected === "1") {
    pollConnectionStatus().then((data) => {
      if (data.connected) {
        setNote(t("connect.success"), "ok");
      } else {
        setNote(t("connect.failed"), "error");
      }
    });
    params.delete("connected");
    const qs = params.toString();
    const next = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
    window.history.replaceState({}, "", next);
  } else if (connected === "0") {
    setNote(t("connect.failed"), "error");
    params.delete("connected");
    const qs = params.toString();
    const next = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
    window.history.replaceState({}, "", next);
  }
}

function handleCreditsQuery() {
  const params = new URLSearchParams(window.location.search);
  const credits = params.get("credits");
  if (credits === "1") {
    fetchCredits().then(() => setNote(t("credits.paid"), "ok"));
    params.delete("credits");
    const qs = params.toString();
    window.history.replaceState({}, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
  } else if (credits === "0") {
    setNote(t("credits.cancelled"), "error");
    params.delete("credits");
    const qs = params.toString();
    window.history.replaceState({}, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
  }
}

function setProgress(active) {
  const progress = document.getElementById("progress");
  if (progress) progress.hidden = !active;
}

function csvEscape(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}

function downloadCsv(rows) {
  const cols = [
    "first_name",
    "last_name",
    "full_name",
    "job_title",
    "company_name",
    "location",
    "linkedin_url",
    "sales_nav_id",
    "open_profile",
    "connection_degree",
  ];
  const lines = [cols.join(",")];
  rows.forEach((row) => {
    lines.push(cols.map((c) => csvEscape(row[c])).join(","));
  });
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sales-navigator-export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function renderPreview(rows) {
  const tbody = document.getElementById("preview-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  rows.slice(0, 10).forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(row.full_name || "")}</td>
      <td>${escapeHtml(row.job_title || "")}</td>
      <td>${escapeHtml(row.company_name || "")}</td>
      <td>${escapeHtml(row.location || "")}</td>`;
    tbody.appendChild(tr);
  });
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function getChallenge() {
  const res = await fetch("/api/challenge.php", { credentials: "same-origin" });
  const data = await res.json();
  if (!res.ok || !data.ok || !data.challenge) {
    throw new Error(t("msg.challenge"));
  }
  await new Promise((r) => setTimeout(r, data.min_wait_ms || 1200));
  return String(data.challenge);
}

async function runExport() {
  if (!isConnected) {
    setNote(t("connect.required"), "error");
    return;
  }
  const mode = document.querySelector(".mode-btn.is-active")?.dataset.mode || "list";
  const listUrl = document.getElementById("list-url")?.value.trim() || "";
  const searchUrl = document.getElementById("search-url")?.value.trim() || "";
  const limit = parseInt(document.getElementById("export-limit")?.value || "25", 10);
  const honeypot = document.getElementById("company_url")?.value || "";

  if (mode === "list" && !listUrl) {
    setNote(lang === "es" ? "Pega la URL de la lista." : "Paste a list URL.", "error");
    return;
  }
  if (mode === "search" && !searchUrl) {
    setNote(lang === "es" ? "Pega la URL de búsqueda." : "Paste a search URL.", "error");
    return;
  }

  setNote(t("msg.exporting"), "ok");
  setProgress(true);
  document.getElementById("results")?.setAttribute("hidden", "");
  document.getElementById("export-submit").disabled = true;

  try {
    const challenge = await getChallenge();
    const body = {
      challenge,
      company_url: honeypot,
      limit,
    };
    if (mode === "list") body.list_url = listUrl;
    else body.search_url = searchUrl;

    const res = await fetch("/api/salesnav-export.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (res.status === 429) {
      throw new Error(t("msg.rateLimit"));
    }
    if (res.status === 402 && data.needs_payment) {
      await startStripeCheckout("100");
      throw new Error(t("credits.insufficient"));
    }
    if (data.needs_connect) {
      renderConnectionStatus({ connected: false });
      throw new Error(t("connect.required"));
    }
    if (!res.ok || !data.ok) {
      throw new Error(data.error || t("msg.generic"));
    }

    lastRows = data.rows || [];
    if (!lastRows.length) {
      throw new Error(t("msg.empty"));
    }

    await fetchCredits();

    renderPreview(lastRows);
    const summary = document.getElementById("results-summary");
    if (summary) {
      summary.textContent = t("results.summary", {
        count: data.count || lastRows.length,
        seconds: data.seconds || 1,
      });
    }
    document.getElementById("results")?.removeAttribute("hidden");
    setNote("", "ok");
    document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    setNote(err.message || t("msg.generic"), "error");
  } finally {
    setProgress(false);
    document.getElementById("export-submit").disabled = false;
  }
}

function initModeSwitch() {
  const listWrap = document.getElementById("list-wrap");
  const searchWrap = document.getElementById("search-wrap");
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      const mode = btn.dataset.mode;
      if (listWrap) listWrap.hidden = mode !== "list";
      if (searchWrap) searchWrap.hidden = mode !== "search";
    });
  });
}

function setContactNote(text, tone = "ok") {
  const note = document.getElementById("contact-note");
  if (!note) return;
  note.hidden = !text;
  note.dataset.tone = tone;
  note.textContent = text || "";
}

async function loadContactChallenge() {
  const res = await fetch("/api/contact-challenge.php", { credentials: "same-origin" });
  const data = await res.json();
  if (!res.ok || !data.ok || !data.challenge) {
    throw new Error(t("msg.challenge"));
  }
  document.getElementById("captcha-question").textContent = data.captcha_question || "…";
  document.getElementById("captcha-id").value = data.captcha_id || "";
  document.getElementById("captcha-answer").value = "";
  await new Promise((r) => setTimeout(r, data.min_wait_ms || 1200));
  return String(data.challenge);
}

function initContactForm() {
  const form = document.getElementById("contact-form");
  if (!form) return;

  loadContactChallenge()
    .then((token) => {
      contactChallengeToken = token;
    })
    .catch(() => setContactNote(t("msg.challenge"), "error"));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setContactNote("", "ok");
    const tier = document.getElementById("contact-tier")?.value || "basic";
    const volume = document.getElementById("contact-volume")?.value || "";
    const message = `Sales Navigator export · tier: ${tier}`;

    try {
      if (!contactChallengeToken) {
        contactChallengeToken = await loadContactChallenge();
      }
      const res = await fetch("/api/contact.php", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("contact-name").value.trim(),
          company: document.getElementById("contact-company").value.trim(),
          email: document.getElementById("contact-email").value.trim(),
          volume,
          message,
          source: "salesnav",
          challenge: contactChallengeToken,
          captcha_id: document.getElementById("captcha-id").value,
          captcha_answer: document.getElementById("captcha-answer").value.trim(),
          website: document.getElementById("contact-website").value,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || t("msg.generic"));
      }
      document.getElementById("contact-fields").hidden = true;
      document.getElementById("contact-success").hidden = false;
      contactChallengeToken = "";
    } catch (err) {
      setContactNote(err.message || t("msg.generic"), "error");
      loadContactChallenge()
        .then((token) => {
          contactChallengeToken = token;
        })
        .catch(() => {});
    }
  });

  document.getElementById("contact-again")?.addEventListener("click", () => {
    document.getElementById("contact-success").hidden = true;
    document.getElementById("contact-fields").hidden = false;
    form.reset();
    loadContactChallenge()
      .then((token) => {
        contactChallengeToken = token;
      })
      .catch(() => {});
  });
}

document.getElementById("y").textContent = new Date().getFullYear();

initLang();
initModeSwitch();
initContactForm();
handleConnectQuery();
handleCreditsQuery();
fetchCredits();
fetchConnectionStatus().catch(() => renderConnectionStatus({ connected: false }));

document.getElementById("connect-btn")?.addEventListener("click", () => startConnect(false));
document.getElementById("reconnect-btn")?.addEventListener("click", () => startConnect(true));
document.getElementById("buy-credits-btn")?.addEventListener("click", () => startStripeCheckout("100"));
document.getElementById("disconnect-btn")?.addEventListener("click", () => disconnectLinkedIn());

document.getElementById("export-form")?.addEventListener("submit", (e) => {
  e.preventDefault();
  runExport();
});

document.getElementById("download-csv")?.addEventListener("click", () => {
  if (lastRows.length) downloadCsv(lastRows);
});

document.getElementById("export-another")?.addEventListener("click", () => {
  document.getElementById("results")?.setAttribute("hidden", "");
  lastRows = [];
  setNote("", "ok");
  window.scrollTo({ top: 0, behavior: "smooth" });
});
