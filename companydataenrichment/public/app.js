document.getElementById("y").textContent = String(new Date().getFullYear());

const I18N = {
  en: {
    "nav.companies": "Companies",
    "nav.salesnav": "Sales Navigator",
    "nav.allProducts": "← All products",
    "hub.badge1": "Free demo",
    "hub.badge2": "No credit card",
    "hub.title": "B2B data enrichment for growth teams",
    "hub.lede":
      "Two problems, two solutions. Enrich LinkedIn company data for paid media audiences or ABM campaigns. Export Sales Navigator lists for outbound.",
    "hub.ctaCompanies": "Try Companies",
    "hub.ctaSalesnav": "Try Sales Navigator",
    "hub.logos": "Paid media · CRM ops · SDR & outbound",
    "hub.companies.label": "Companies",
    "hub.companies.title": "Paid Media Audiences",
    "hub.companies.body":
      "Turn a Spanish legal or brand name into LinkedIn, website, domain and firmographics for CRM and ad platforms.",
    "hub.companies.p1": "Free single lookup & batch demo (up to 10)",
    "hub.companies.p2": "Volume from €0.18 / record",
    "hub.companies.cta": "Start free demo",
    "hub.salesnav.label": "Sales Navigator Export",
    "hub.salesnav.title": "CSV export",
    "hub.salesnav.stat": "25",
    "hub.salesnav.statLabel": "free demo leads",
    "hub.salesnav.body":
      "Export saved lead lists and people searches from your Sales Navigator seat.",
    "hub.salesnav.p1": "Basic · Enriched · Mail tiers",
    "hub.salesnav.p2": "Credits from €20",
    "hub.salesnav.cta": "Export CSV",
    "companies.kicker": "Companies · Paid Media Audiences",
    "companies.sectionTitle": "Resolve Spanish companies into audience-ready identities",
    "companies.sectionLede":
      "Enrich CRM rows, outreach lists and paid media audiences from a legal name or brand — with LinkedIn, website, domain and firmographics in one record.",
    "salesnav.kicker": "Sales Navigator Export",
    "salesnav.sectionTitle": "Export SN lists and people searches to CSV",
    "salesnav.sectionLede":
      "Turn saved Sales Navigator lead lists and people searches into a CRM-ready CSV — connect your LinkedIn seat, paste a list or search URL, and download.",
    "salesnav.p1": "<strong>Fields:</strong> name, job title, company, location, LinkedIn profile URL",
    "salesnav.p2": "<strong>Sources:</strong> saved lead lists and people searches in Sales Navigator",
    "salesnav.p3": "<strong>Tiers:</strong> simple CSV export now · enriched profile and email options on request",
    "salesnav.cta": "Open Sales Navigator Export",
    "salesnav.pricing": "View SN pricing tiers",
    "hero.kicker": "Enter a company legal or brand name.",
    "hero.title": "Enrich CRM, outreach and paid media.",
    "hero.lede":
      "We resolve Spanish company names into one usable identity — LinkedIn, website, domain, phone, HQ and firmographics — ready for enrichment workflows.",
    "hero.coverage":
      'Currently optimized for companies incorporated in <strong>Spain</strong>. Support for other territories is under evaluation.',
    "mode.single": "Single",
    "mode.batch": "Batch (demo · up to 10)",
    "form.companyLabel": "Company legal name or brand",
    "form.placeholder": "e.g. Albrok Mediacion S.A.",
    "form.batchLabel": "One company per line",
    "form.batchPlaceholder": "One company per line — free demo max 10",
    "form.submit": "Resolve company",
    "form.processing": "Processing…",
    "examples.label": "Try:",
    "examples.hint":
      "Demo is free for single lookups and batches of up to 10. Scores below ~60% usually need a human review.",
    "progress.s1": "Normalizing company name",
    "progress.s2": "Searching web & LinkedIn signals",
    "progress.s3": "Enriching top matches",
    "progress.s4": "Scoring confidence",
    "progress.done": "Done",
    "results.title": "Resolved identity",
    "export.another": "Resolve another",
    "export.json": "Copy JSON",
    "export.csv": "Download CSV",
    "export.copied": "JSON copied",
    "export.volume": "Request volume pricing",
    "results.evidence": "Evidence",
    "pricing.kicker": "Volume pricing",
    "pricing.title": 'From <strong>€0.18</strong> / enriched record',
    "pricing.lede":
      "Free demo on this page (single or batch up to 10). For CRM lists, campaigns or API volume, tell us your use case and we will send a quote.",
    "pricing.b1": "LinkedIn company page, website, domain and firmographics",
    "pricing.b2": "Confidence score + evidence on every delivery",
    "pricing.b3": "Spain first · API and batch exports available",
    "contact.title": "Request pricing",
    "contact.name": "Name",
    "contact.company": "Company",
    "contact.email": "Corporate email",
    "contact.volume": "Enriched records",
    "contact.volumePlaceholder": "Select volume…",
    "contact.volume.1_500": "1 – 500",
    "contact.volume.500_1k": "500 – 1,000",
    "contact.volume.1k_10k": "1,000 – 10,000",
    "contact.volume.10k_50k": "10,000 – 50,000",
    "contact.volume.50k_200k": "50,000 – 200,000",
    "contact.captcha": "Anti-spam — what is",
    "contact.submit": "Send request",
    "contact.sending": "Sending…",
    "contact.ok": "Thanks — we will reply to your corporate email shortly.",
    "contact.okKicker": "Request sent",
    "contact.okTitle": "Thanks — we got your message.",
    "contact.okBody":
      "We will reply to your corporate email shortly about pricing and API access.",
    "contact.again": "Send another request",
    "contact.err": "Could not send. Please email hello@parvusmedia.com",
    "contact.captchaFail": "Incorrect captcha. Please try again.",
    "contact.privacy":
      'We will only use these details to reply about CompanyDataEnrichment. <a href="/privacy.html">Privacy policy</a>.',
    "usecases.title": "Who it's for",
    "usecases.lede":
      'Built for teams that start from a legal name or incomplete CRM row and need a usable company identity — <strong>LinkedIn, website and firmographics</strong> — without manual Google digging.',
    "usecases.crm.title": "CRM data quality",
    "usecases.crm.body":
      'Fill gaps on accounts that only have a razón social: official website, LinkedIn company page, domain, headcount and HQ. Typical CRM lists miss <strong>30–60%</strong> of those fields before enrichment.',
    "usecases.outbound.title": "Campaigns & LinkedIn prospecting",
    "usecases.outbound.body":
      'Turn legal names into <strong>LinkedIn company URLs</strong> and web domains for list building, ABM, nurture and sales outreach — so marketing and SDR teams prospect from a verified firm page, not a guess.',
    "usecases.research.title": "Research & ops teams",
    "usecases.research.body":
      'Accelerate desk research, partner screening and market mapping when analysts need <strong>one consolidated record</strong> per company instead of five open tabs.',
    "usecases.compliance.title": "Vendor / supplier screening",
    "usecases.compliance.body":
      'Cross-check public presence (web + LinkedIn + HQ signals) before onboarding a supplier or account — with an explicit <strong>confidence score</strong> on every delivery.',
    "trust.title": "Public data & compliance",
    "trust.lede":
      'We enrich from <strong>publicly available company signals</strong> (web + LinkedIn company pages), unify them and return one deliverable record with a confidence score.',
    "trust.p1":
      'We resolve firm identity from <strong>public web and LinkedIn company pages</strong>, then unify those signals into one deliverable record.',
    "trust.p2":
      'Matches can still be wrong. Deterministic scoring plus AI validation produce a <strong>confidence score</strong> so you can accept, review or reject each row.',
    "trust.p3":
      'One input name → <strong>one unified output record</strong> (LinkedIn, website, domain, firmographics and evidence), ready for CRM or campaign use.',
    "trust.p4":
      'Not a substitute for legal, KYC or compliance diligence — treat every match as <strong>assistive data</strong> to review.',
    "trust.privacy": "Terms & privacy policy",
    "api.title": "API access",
    "api.lede":
      "Wire enrichment into your CRM or pipeline. Spain coverage first. Free demo above · volume from €0.18 / record.",
    "api.cta": "Request API access",
    "cross.sn":
      'Also export leads from Sales Navigator? <a href="/salesnav/">Sales Navigator Export →</a>',
    "footer.tag": "Companies · Sales Navigator export · Spain coverage first",
    "footer.privacy": "Privacy",
    "msg.resolvedOne": "Identity resolved for “{name}” in {seconds}s.",
    "msg.resolvedMany": "Resolved {count} companies in {seconds}s.",
    "msg.cachedOne": "Identity for “{name}” served from recent cache.",
    "msg.cachedMany": "{count} companies served from recent cache.",
    "msg.empty": "No identity found for “{name}”.",
    "msg.ambiguous":
      "Match is ambiguous. Try the commercial brand name, or add city if you know it.",
    "msg.notFound":
      "No reliable LinkedIn match. Try the brand name used publicly, without legal form (S.A., S.L.).",
    "msg.partial": "Partial match — website found, LinkedIn still weak.",
    "msg.startFail": "Could not start processing. Please try again.",
    "msg.generic": "Something went wrong.",
    "msg.timeout": "This is taking longer than expected. Please try again in a moment.",
    "msg.rateLimit": "Too many searches from this session. Please wait and try again.",
    "msg.challenge": "Security check failed. Refresh the page and try again.",
    "msg.needCompany": "Enter at least one company name.",
    "msg.batchLimit": "Batch limit is 10 companies.",
    "stage.1": "Processing — normalizing company name…",
    "stage.2": "Processing — searching web & LinkedIn signals…",
    "stage.3": "Processing — enriching top matches…",
    "stage.4": "Processing — scoring confidence…",
    "stage.5": "Processing — finalizing identity…",
  },
  es: {
    "nav.companies": "Empresas",
    "nav.salesnav": "Sales Navigator",
    "nav.allProducts": "← Todos los productos",
    "hub.badge1": "Demo gratis",
    "hub.badge2": "Sin tarjeta",
    "hub.title": "Enriquecimiento B2B para equipos de crecimiento",
    "hub.lede":
      "Dos problemas, dos soluciones. Enriquece datos de empresa en LinkedIn para audiencias de paid media o campañas ABM. Exporta listas de Sales Navigator para outbound.",
    "hub.ctaCompanies": "Probar Companies",
    "hub.ctaSalesnav": "Probar Sales Navigator",
    "hub.logos": "Paid media · CRM · SDR y outbound",
    "hub.companies.label": "Companies",
    "hub.companies.title": "Paid Media Audiences",
    "hub.companies.body":
      "De razón social o marca a LinkedIn, web, dominio y firmográficos para CRM y plataformas de ads.",
    "hub.companies.p1": "Demo gratis: consulta individual o lote (hasta 10)",
    "hub.companies.p2": "Volumen desde €0,18 / registro",
    "hub.companies.cta": "Probar demo gratis",
    "hub.salesnav.label": "Sales Navigator Export",
    "hub.salesnav.title": "Exportación CSV",
    "hub.salesnav.stat": "25",
    "hub.salesnav.statLabel": "leads gratis en demo",
    "hub.salesnav.body":
      "Exporta listas guardadas y búsquedas de personas desde tu seat de Sales Navigator.",
    "hub.salesnav.p1": "Planes Basic · Enriched · Mail",
    "hub.salesnav.p2": "Créditos desde €20",
    "hub.salesnav.cta": "Exportar CSV",
    "companies.kicker": "Companies · Paid Media Audiences",
    "companies.sectionTitle": "Resuelve empresas españolas en identidades listas para audiencias",
    "companies.sectionLede":
      "Enriquece filas de CRM, listas de outreach y audiencias paid media desde razón social o marca — con LinkedIn, web, dominio y firmográficos en un solo registro.",
    "salesnav.kicker": "Sales Navigator Export",
    "salesnav.sectionTitle": "Exporta listas SN y búsquedas a CSV",
    "salesnav.sectionLede":
      "Convierte listas guardadas y búsquedas de personas de Sales Navigator en un CSV listo para CRM — conecta tu cuenta LinkedIn, pega la URL y descarga.",
    "salesnav.p1": "<strong>Campos:</strong> nombre, cargo, empresa, ubicación, URL de perfil LinkedIn",
    "salesnav.p2": "<strong>Fuentes:</strong> listas de leads guardadas y búsquedas de personas en Sales Navigator",
    "salesnav.p3": "<strong>Tiers:</strong> export CSV simple ya disponible · enriquecido y email bajo petición",
    "salesnav.cta": "Abrir Sales Navigator Export",
    "salesnav.pricing": "Ver tiers de precio SN",
    "hero.kicker": "Introduce una razón social o marca.",
    "hero.title": "Enriquece CRM, outreach y paid media.",
    "hero.lede":
      "Resolvemos nombres de empresas españolas en una identidad usable — LinkedIn, web, dominio, teléfono, sede y firmográficos — lista para flujos de enriquecimiento.",
    "hero.coverage":
      'Por ahora está optimizado para empresas constituidas en <strong>España</strong>. Estamos evaluando la ampliación a otros países.',
    "mode.single": "Individual",
    "mode.batch": "Lote (demo · máx. 10)",
    "form.companyLabel": "Razón social o marca",
    "form.placeholder": "ej. Albrok Mediacion S.A.",
    "form.batchLabel": "Una empresa por línea",
    "form.batchPlaceholder": "Una empresa por línea — demo gratis máx. 10",
    "form.submit": "Resolver empresa",
    "form.processing": "Procesando…",
    "examples.label": "Probar:",
    "examples.hint":
      "La demo es gratuita para consultas individuales y lotes de hasta 10. Un score por debajo de ~60% suele requerir revisión humana.",
    "progress.s1": "Normalizando el nombre",
    "progress.s2": "Buscando señales en web y LinkedIn",
    "progress.s3": "Enriqueciendo los mejores candidatos",
    "progress.s4": "Calculando la confianza",
    "progress.done": "Listo",
    "results.title": "Identidad resuelta",
    "export.another": "Resolver otra",
    "export.json": "Copiar JSON",
    "export.csv": "Descargar CSV",
    "export.copied": "JSON copiado",
    "export.volume": "Pedir pricing por volumen",
    "results.evidence": "Evidencia",
    "pricing.kicker": "Pricing por volumen",
    "pricing.title": 'Desde <strong>0,18 €</strong> / registro enriquecido',
    "pricing.lede":
      "Demo gratis en esta página (individual o lote de hasta 10). Para listas CRM, campañas o volumen vía API, cuéntanos el caso y te enviamos presupuesto.",
    "pricing.b1": "Página LinkedIn de empresa, web, dominio y firmográficos",
    "pricing.b2": "Confidence score + evidencia en cada entrega",
    "pricing.b3": "España primero · API y exportaciones por lote",
    "contact.title": "Solicitar pricing",
    "contact.name": "Nombre",
    "contact.company": "Empresa",
    "contact.email": "Email corporativo",
    "contact.volume": "Registros enriquecidos",
    "contact.volumePlaceholder": "Selecciona volumen…",
    "contact.volume.1_500": "1 – 500",
    "contact.volume.500_1k": "500 – 1.000",
    "contact.volume.1k_10k": "1.000 – 10.000",
    "contact.volume.10k_50k": "10.000 – 50.000",
    "contact.volume.50k_200k": "50.000 – 200.000",
    "contact.captcha": "Anti-spam — ¿cuánto es",
    "contact.submit": "Enviar solicitud",
    "contact.sending": "Enviando…",
    "contact.ok": "Gracias — te responderemos al email corporativo en breve.",
    "contact.okKicker": "Solicitud enviada",
    "contact.okTitle": "Gracias — hemos recibido tu mensaje.",
    "contact.okBody":
      "Te responderemos al email corporativo en breve con pricing y acceso API.",
    "contact.again": "Enviar otra solicitud",
    "contact.err": "No se pudo enviar. Escribe a hello@parvusmedia.com",
    "contact.captchaFail": "Captcha incorrecto. Inténtalo de nuevo.",
    "contact.privacy":
      'Solo usaremos estos datos para responder sobre CompanyDataEnrichment. <a href="/privacy.html">Política de privacidad</a>.',
    "usecases.title": "Para quién es",
    "usecases.lede":
      'Pensado para equipos que parten de una razón social o de un registro incompleto en el CRM y necesitan una identidad de empresa usable — <strong>LinkedIn, web y firmográficos</strong> — sin buscar a mano en Google.',
    "usecases.crm.title": "Mejorar datos de CRM",
    "usecases.crm.body":
      'Completa cuentas que solo tienen razón social: web oficial, página de LinkedIn, dominio, plantilla y sede. En listas CRM típicas faltan entre un <strong>30% y un 60%</strong> de esos campos antes del enriquecimiento.',
    "usecases.outbound.title": "Campañas y prospección en LinkedIn",
    "usecases.outbound.body":
      'Convierte razones sociales en <strong>URLs de empresa en LinkedIn</strong> y dominios web para listados, ABM, nurturing y outreach. Marketing y ventas prospectan desde una ficha verificada, no desde una conjetura.',
    "usecases.research.title": "Equipos de research y operaciones",
    "usecases.research.body":
      'Acelera la investigación de escritorio, el screening de partners y el mapeo de mercado cuando hace falta <strong>un registro consolidado</strong> por empresa, no cinco pestañas abiertas.',
    "usecases.compliance.title": "Screening de proveedores",
    "usecases.compliance.body":
      'Contrasta la presencia pública (web + LinkedIn + señales de sede) antes de dar de alta un proveedor o una cuenta, con un <strong>score de confianza</strong> explícito en cada entrega.',
    "trust.title": "Datos públicos y compliance",
    "trust.lede":
      'Enriquecemos a partir de <strong>señales públicas de empresa</strong> (web + páginas de empresa en LinkedIn), las unificamos y devolvemos un registro entregable con confidence score.',
    "trust.p1":
      'Resolvemos la identidad de empresa desde <strong>web pública y páginas de empresa en LinkedIn</strong>, y unificamos esas señales en un único registro entregable.',
    "trust.p2":
      'Aun así puede haber errores. El scoring determinista y la validación con IA generan un <strong>confidence score</strong> para aceptar, revisar o descartar cada fila.',
    "trust.p3":
      'Un nombre de entrada → <strong>un registro unificado</strong> de salida (LinkedIn, web, dominio, firmográficos y evidencia), listo para CRM o campañas.',
    "trust.p4":
      'No sustituye la diligencia legal, KYC o de compliance: cada match es <strong>dato asistido</strong> que conviene revisar.',
    "trust.privacy": "Términos y política de privacidad",
    "api.title": "Acceso a la API",
    "api.lede":
      "Integra el enriquecimiento en tu CRM o pipeline. Cobertura inicial en España. Demo gratis arriba · volumen desde 0,18 € / registro.",
    "api.cta": "Solicitar acceso API",
    "cross.sn":
      '¿También exportas leads de Sales Navigator? <a href="/salesnav/">Sales Navigator Export →</a>',
    "footer.tag": "Companies · Sales Navigator export · cobertura España primero",
    "footer.privacy": "Privacidad",
    "msg.resolvedOne": "Identidad resuelta para “{name}” en {seconds}s.",
    "msg.resolvedMany": "Se han resuelto {count} empresas en {seconds}s.",
    "msg.cachedOne": "Identidad de “{name}” servida desde caché reciente.",
    "msg.cachedMany": "{count} empresas servidas desde caché reciente.",
    "msg.empty": "No se ha encontrado identidad para “{name}”.",
    "msg.ambiguous":
      "El resultado es ambiguo. Prueba con la marca comercial o añade la ciudad si la conoces.",
    "msg.notFound":
      "No hay un perfil de LinkedIn fiable. Prueba con la marca pública, sin forma societaria (S.A., S.L.).",
    "msg.partial": "Resultado parcial: hay web, pero el LinkedIn no es suficientemente sólido.",
    "msg.startFail": "No se ha podido iniciar el proceso. Inténtalo de nuevo.",
    "msg.generic": "Ha ocurrido un error.",
    "msg.timeout": "Está tardando más de lo habitual. Vuelve a intentarlo en unos momentos.",
    "msg.rateLimit": "Demasiadas búsquedas en esta sesión. Espera un poco e inténtalo de nuevo.",
    "msg.challenge": "Falló la comprobación de seguridad. Recarga la página e inténtalo de nuevo.",
    "msg.needCompany": "Introduce al menos un nombre de empresa.",
    "msg.batchLimit": "El lote admite un máximo de 10 empresas.",
    "stage.1": "Procesando: normalizando el nombre…",
    "stage.2": "Procesando: buscando señales en web y LinkedIn…",
    "stage.3": "Procesando: enriqueciendo candidatos…",
    "stage.4": "Procesando: calculando la confianza…",
    "stage.5": "Procesando: cerrando la identidad…",
  },
};

let lang = localStorage.getItem("cde_lang") || "en";
let mode = "single";
let lastResults = [];
let progressTimer = null;
let progressValue = 0;
let resolveStartedAt = 0;

const form = document.getElementById("resolve-form");
const note = document.getElementById("form-note");
const button = form.querySelector('button[type="submit"]');
const companyInput = document.getElementById("company");
const batchInput = document.getElementById("companies");
const singleWrap = document.getElementById("single-wrap");
const batchWrap = document.getElementById("batch-wrap");
const results = document.getElementById("results");
const resultsBody = document.getElementById("results-body");
const exportActions = document.getElementById("export-actions");
const progress = document.getElementById("progress");
const progressLabel = document.getElementById("progress-label");
const progressPct = document.getElementById("progress-pct");
const progressFill = document.getElementById("progress-fill");
const progressBar = document.getElementById("progress-bar");
const progressSteps = document.getElementById("progress-steps");

function t(key, vars) {
  let text = (I18N[lang] && I18N[lang][key]) || (I18N.en[key] || key);
  if (vars) {
    Object.keys(vars).forEach((k) => {
      text = text.replaceAll("{" + k + "}", String(vars[k]));
    });
  }
  return text;
}

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.innerHTML = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const active = btn.dataset.lang === lang;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if (!button.disabled) button.textContent = t("form.submit");
}

function friendlyError(message) {
  const raw = String(message || t("msg.generic"));
  if (/apify|actor|token|dataset|run id/i.test(raw)) {
    return t("msg.startFail");
  }
  return raw;
}

function setNote(text, tone) {
  note.hidden = !text;
  note.dataset.tone = tone || "ok";
  note.textContent = text || "";
}

function setBusy(busy) {
  button.disabled = busy;
  button.textContent = busy ? t("form.processing") : t("form.submit");
  companyInput.disabled = busy;
  batchInput.disabled = busy;
  document.querySelectorAll(".chip, .mode-btn").forEach((el) => {
    el.disabled = busy;
  });
}

function scrollInto(el) {
  if (!el) return;
  requestAnimationFrame(() => {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function setProgressVisual(pct) {
  const value = Math.max(0, Math.min(100, Math.round(pct)));
  progressValue = value;
  progressFill.style.width = value + "%";
  progressPct.textContent = value + "%";
  progressBar.setAttribute("aria-valuenow", String(value));

  const stageKey =
    value >= 100
      ? "progress.done"
      : value <= 18
        ? "stage.1"
        : value <= 45
          ? "stage.2"
          : value <= 72
            ? "stage.3"
            : value <= 92
              ? "stage.4"
              : "stage.5";
  progressLabel.textContent = t(stageKey);

  const stepIndex =
    value < 20 ? 1 : value < 48 ? 2 : value < 75 ? 3 : value < 100 ? 4 : 4;
  progressSteps.querySelectorAll("li").forEach((li) => {
    const n = Number(li.dataset.step);
    li.classList.toggle("is-done", n < stepIndex || value >= 100);
    li.classList.toggle("is-active", n === stepIndex && value < 100);
  });
}

function setWorkspace(active) {
  document.body.classList.toggle("has-workspace", !!active);
}

function startProgress() {
  stopProgress();
  setWorkspace(true);
  progress.hidden = false;
  setProgressVisual(4);
  scrollInto(progress);
  const started = Date.now();
  progressTimer = setInterval(() => {
    const elapsed = Date.now() - started;
    let target;
    if (elapsed < 8000) target = 8 + (elapsed / 8000) * 22;
    else if (elapsed < 20000) target = 30 + ((elapsed - 8000) / 12000) * 28;
    else if (elapsed < 40000) target = 58 + ((elapsed - 20000) / 20000) * 24;
    else target = Math.min(92, 82 + ((elapsed - 40000) / 60000) * 10);
    if (progressValue < target) {
      setProgressVisual(progressValue + Math.max(0.4, (target - progressValue) * 0.12));
    }
  }, 200);
}

function completeProgress() {
  stopProgress(false);
  setProgressVisual(100);
}

function stopProgress(hide) {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  if (hide) progress.hidden = true;
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function linkOrDash(url, label) {
  if (!url) return "—";
  return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label || url)}</a>`;
}

function formatNumber(value) {
  if (value == null || value === "") return null;
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  return n.toLocaleString(lang === "es" ? "es-ES" : "en-US");
}

function field(label, valueHtml) {
  if (!valueHtml || valueHtml === "—") return "";
  return `<div class="field"><span class="label">${esc(label)}</span><span class="value">${valueHtml}</span></div>`;
}

function confidenceBar(confidence, status) {
  const pct = Math.max(0, Math.min(100, Number(confidence) || 0));
  const tone =
    pct >= 78 ? "high" : pct >= 60 ? "mid" : pct >= 40 ? "low" : "poor";
  return `
    <div class="confidence-block tone-${tone}">
      <div class="confidence-top">
        <span class="badge">${esc(status || "unknown")}</span>
        <strong class="score-chip">${esc(pct)}%</strong>
      </div>
      <div class="confidence-track"><div class="confidence-fill" style="width:${pct}%"></div></div>
    </div>`;
}

function statusHint(status) {
  const s = String(status || "").toLowerCase();
  if (s === "ambiguous") return `<p class="status-hint">${esc(t("msg.ambiguous"))}</p>`;
  if (s === "not_found") return `<p class="status-hint">${esc(t("msg.notFound"))}</p>`;
  if (s === "partial") return `<p class="status-hint">${esc(t("msg.partial"))}</p>`;
  return "";
}

function renderOneResult(result, fallbackName) {
  if (!result) {
    return `<p class="result-empty">${esc(t("msg.empty", { name: fallbackName || "" }))}</p>`;
  }

  const company = result.legal_name || fallbackName || "";
  const employees =
    result.employee_count != null
      ? formatNumber(result.employee_count) +
        (result.employee_range ? ` <span class="muted">(${esc(result.employee_range)})</span>` : "")
      : result.employee_range
        ? esc(result.employee_range)
        : null;
  const industries =
    Array.isArray(result.industries) && result.industries.length
      ? esc(result.industries.join(", "))
      : result.industry
        ? esc(result.industry)
        : null;
  const specialties =
    Array.isArray(result.specialties) && result.specialties.length
      ? esc(result.specialties.join(", "))
      : null;

  const logo = result.logo
    ? `<div class="result-brand"><img src="${esc(result.logo)}" alt="" width="56" height="56" loading="lazy" /><div><strong>${esc(
        result.commercial_name || company
      )}</strong>${
        result.tagline ? `<p class="tagline">${esc(result.tagline)}</p>` : ""
      }</div></div>`
    : result.tagline
      ? `<p class="tagline">${esc(result.tagline)}</p>`
      : "";

  return `
    <article class="result-card">
      ${logo}
      ${confidenceBar(result.confidence, result.match_status)}
      ${statusHint(result.match_status)}
      <div class="result-grid">
        ${field("Legal name", esc(company))}
        ${field("Commercial name", result.commercial_name ? esc(result.commercial_name) : null)}
        ${field("LinkedIn", linkOrDash(result.linkedin_url))}
        ${field("Website", linkOrDash(result.website, result.website))}
        ${field("Domain", result.domain ? esc(result.domain) : null)}
        ${field("Founded", result.founded_year != null ? esc(result.founded_year) : null)}
        ${field("Industry", industries)}
        ${field("Employees", employees)}
        ${field("Followers", result.followers != null ? formatNumber(result.followers) : null)}
        ${field("Phone", result.phone ? esc(result.phone) : null)}
        ${field("Headquarters", result.headquarters ? esc(result.headquarters) : null)}
        ${field("Specialties", specialties)}
        ${field("Relationship", result.relationship ? esc(result.relationship) : null)}
      </div>
      ${
        result.description
          ? `<details class="result-more"><summary>About</summary><p>${esc(result.description)}</p></details>`
          : ""
      }
      ${
        result.evidence_summary
          ? `<div class="evidence-block"><h4>${esc(t("results.evidence"))}</h4><p>${esc(result.evidence_summary)}</p></div>`
          : ""
      }
      ${result.error ? `<p class="result-error">${esc(result.error)}</p>` : ""}
    </article>`;
}

function renderResults(list, requestedNames) {
  lastResults = Array.isArray(list) ? list : [];
  setWorkspace(true);
  results.hidden = false;
  exportActions.hidden = lastResults.length === 0;

  if (!lastResults.length) {
    const name = (requestedNames && requestedNames[0]) || "";
    resultsBody.innerHTML = `<p class="result-empty">${esc(t("msg.empty", { name }))}</p>`;
    scrollInto(results);
    return;
  }

  resultsBody.innerHTML = lastResults
    .map((row, i) => renderOneResult(row, requestedNames?.[i]))
    .join("");
  scrollInto(results);
}

function csvEscape(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}

function downloadCsv(rows) {
  const cols = [
    "legal_name",
    "commercial_name",
    "linkedin_url",
    "website",
    "domain",
    "founded_year",
    "industry",
    "employee_count",
    "followers",
    "phone",
    "headquarters",
    "match_status",
    "confidence",
    "relationship",
  ];
  const lines = [cols.join(",")];
  rows.forEach((row) => {
    lines.push(cols.map((c) => csvEscape(row[c])).join(","));
  });
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "companydataenrichment.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function finishWithResults(list, requestedNames, opts = {}) {
  const seconds = Math.max(
    1,
    Math.round((Date.now() - resolveStartedAt) / 1000)
  );
  const cached = !!opts.cached;
  if (list.length > 1) {
    setNote(
      t(cached ? "msg.cachedMany" : "msg.resolvedMany", {
        count: list.length,
        seconds,
      }),
      "ok"
    );
  } else {
    setNote(
      t(cached ? "msg.cachedOne" : "msg.resolvedOne", {
        name: list[0]?.legal_name || requestedNames[0] || "",
        seconds,
      }),
      "ok"
    );
  }
  renderResults(list, requestedNames);
}

async function pollStatus(runId, requestedNames) {
  const maxMs = Math.min(8 * 60 * 1000, 60000 + requestedNames.length * 45000);

  while (Date.now() - resolveStartedAt < maxMs) {
    const res = await fetch(`/api/status.php?runId=${encodeURIComponent(runId)}`, {
      headers: { Accept: "application/json" },
    });
    const data = await res.json();
    if (!res.ok && !data.status) {
      throw new Error(friendlyError(data.error) || t("msg.generic"));
    }

    const status = data.status || "UNKNOWN";
    if (data.finished) {
      if (status === "SUCCEEDED") {
        completeProgress();
        const list = Array.isArray(data.results)
          ? data.results
          : data.result
            ? [data.result]
            : [];
        finishWithResults(list, requestedNames, { cached: false });
        return;
      }
      throw new Error(friendlyError(data.error) || t("msg.generic"));
    }
    await new Promise((r) => setTimeout(r, 2500));
  }
  throw new Error(t("msg.timeout"));
}

function parseCompanies() {
  if (mode === "batch") {
    const lines = String(batchInput.value || "")
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    return [...new Set(lines)];
  }
  const one = String(companyInput.value || "").trim();
  return one ? [one] : [];
}

async function getChallenge() {
  const res = await fetch("/api/challenge.php", {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const data = await res.json();
  if (!res.ok || !data.ok || !data.challenge) {
    throw new Error(t("msg.challenge"));
  }
  const wait = Math.max(0, Number(data.min_wait_ms) || 1200);
  await new Promise((r) => setTimeout(r, wait));
  return String(data.challenge);
}

async function runResolve(names, opts = {}) {
  if (!names.length) {
    setNote(t("msg.needCompany"), "error");
    return;
  }
  if (names.length > 10) {
    setNote(t("msg.batchLimit"), "error");
    return;
  }

  const origin = opts.origin === "chip" ? "chip" : "form";

  results.hidden = true;
  resultsBody.innerHTML = "";
  exportActions.hidden = true;
  lastResults = [];
  setNote("", "ok");
  setBusy(true);
  resolveStartedAt = Date.now();
  startProgress();

  try {
    const challenge = await getChallenge();
    const honeypot = String(document.getElementById("company_url")?.value || "");
    const meta = { mode, ui_lang: lang, origin };
    const body =
      names.length === 1
        ? { company: names[0], challenge, company_url: honeypot, ...meta }
        : {
            companies: names.map((legal_name) => ({ legal_name })),
            challenge,
            company_url: honeypot,
            ...meta,
          };

    const res = await fetch("/api/resolve.php", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (res.status === 429) {
      throw new Error(t("msg.rateLimit"));
    }
    if (res.status === 403) {
      throw new Error(t("msg.challenge"));
    }
    if (!res.ok || !data.ok) {
      throw new Error(friendlyError(data.error) || t("msg.startFail"));
    }
    if (data.cached && (Array.isArray(data.results) || data.result)) {
      completeProgress();
      const list = Array.isArray(data.results)
        ? data.results
        : data.result
          ? [data.result]
          : [];
      finishWithResults(list, names, { cached: true });
      return;
    }
    if (!data.runId) {
      throw new Error(t("msg.startFail"));
    }
    await pollStatus(data.runId, names);
  } catch (err) {
    stopProgress(true);
    setNote(friendlyError(err.message) || t("msg.generic"), "error");
    results.hidden = true;
    exportActions.hidden = true;
    lastResults = [];
    setWorkspace(false);
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runResolve(parseCompanies(), { origin: "form" });
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const value = chip.getAttribute("data-example") || "";
    if (!value) return;
    if (mode === "batch") {
      const current = String(batchInput.value || "").trim();
      batchInput.value = current ? current + "\n" + value : value;
    } else {
      companyInput.value = value;
    }
    runResolve([value], { origin: "chip" });
  });
});

document.querySelectorAll(".mode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    mode = btn.dataset.mode === "batch" ? "batch" : "single";
    document.querySelectorAll(".mode-btn").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.mode === mode);
    });
    singleWrap.hidden = mode !== "single";
    batchWrap.hidden = mode !== "batch";
    companyInput.required = mode === "single";
  });
});

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    lang = btn.dataset.lang === "es" ? "es" : "en";
    localStorage.setItem("cde_lang", lang);
    applyI18n();
    if (lastResults.length) renderResults(lastResults);
  });
});

document.getElementById("resolve-another").addEventListener("click", () => {
  results.hidden = true;
  resultsBody.innerHTML = "";
  exportActions.hidden = true;
  lastResults = [];
  stopProgress(true);
  setNote("", "ok");
  setWorkspace(false);
  if (mode === "batch") {
    batchInput.value = "";
    batchInput.focus();
  } else {
    companyInput.value = "";
    companyInput.focus();
  }
  scrollInto(form);
});

document.getElementById("copy-json").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastResults, null, 2));
    setNote(t("export.copied"), "ok");
  } catch {
    setNote(t("msg.generic"), "error");
  }
});

document.getElementById("download-csv").addEventListener("click", () => {
  if (lastResults.length) downloadCsv(lastResults);
});

const contactForm = document.getElementById("contact-form");
const contactFields = document.getElementById("contact-fields");
const contactSuccess = document.getElementById("contact-success");
const contactNote = document.getElementById("contact-note");
const contactSubmit = document.getElementById("contact-submit");
const captchaQuestion = document.getElementById("captcha-question");
const captchaAnswer = document.getElementById("captcha-answer");
const captchaId = document.getElementById("captcha-id");

function setContactNote(text, tone) {
  if (!contactNote) return;
  contactNote.hidden = !text;
  contactNote.dataset.tone = tone || "ok";
  contactNote.textContent = text || "";
}

function showContactSuccess() {
  if (contactFields) contactFields.hidden = true;
  if (contactSuccess) {
    contactSuccess.hidden = false;
    contactSuccess.focus?.();
    contactSuccess.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  setContactNote("", "ok");
}

function showContactForm() {
  if (contactSuccess) contactSuccess.hidden = true;
  if (contactFields) contactFields.hidden = false;
  setContactNote("", "ok");
}

async function loadContactChallenge() {
  if (!captchaQuestion || !captchaId) return null;
  captchaQuestion.textContent = "…";
  captchaId.value = "";
  if (captchaAnswer) captchaAnswer.value = "";
  const res = await fetch("/api/contact-challenge.php", {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const data = await res.json();
  if (!res.ok || !data.ok || !data.challenge) {
    throw new Error(t("msg.challenge"));
  }
  captchaQuestion.textContent = String(data.captcha_question || "?") + " =";
  captchaId.value = String(data.captcha_id || "");
  const wait = Math.max(0, Number(data.min_wait_ms) || 1200);
  return { challenge: String(data.challenge), wait };
}

let contactChallengeToken = "";
let contactChallengeReadyAt = 0;

async function prepareContactForm() {
  try {
    const pack = await loadContactChallenge();
    if (!pack) return;
    contactChallengeToken = pack.challenge;
    contactChallengeReadyAt = Date.now() + pack.wait;
  } catch {
    captchaQuestion.textContent = "!";
    setContactNote(t("msg.challenge"), "error");
  }
}

if (contactForm) {
  prepareContactForm();

  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setContactNote("", "ok");

    const name = String(document.getElementById("contact-name")?.value || "").trim();
    const company = String(document.getElementById("contact-company")?.value || "").trim();
    const email = String(document.getElementById("contact-email")?.value || "").trim();
    const volume = String(document.getElementById("contact-volume")?.value || "").trim();
    const answer = String(captchaAnswer?.value || "").trim();
    const honeypot = String(document.getElementById("contact-website")?.value || "");

    if (!name || !company || !email || !volume || !answer) {
      setContactNote(t("contact.err"), "error");
      return;
    }

    contactSubmit.disabled = true;
    contactSubmit.textContent = t("contact.sending");

    try {
      const delay = Math.max(0, contactChallengeReadyAt - Date.now());
      if (delay) await new Promise((r) => setTimeout(r, delay));

      const res = await fetch("/api/contact.php", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          name,
          company,
          email,
          volume,
          captcha_id: captchaId.value,
          captcha_answer: answer,
          challenge: contactChallengeToken,
          website: honeypot,
          source: "companies-pricing",
        }),
      });
      const data = await res.json();
      if (res.status === 429) {
        throw new Error(t("msg.rateLimit"));
      }
      if (!res.ok || !data.ok) {
        const err = String(data.error || "");
        if (/captcha/i.test(err)) throw new Error(t("contact.captchaFail"));
        throw new Error(err || t("contact.err"));
      }
      setContactNote(t("contact.ok"), "ok");
      contactForm.reset();
      showContactSuccess();
      await prepareContactForm();
    } catch (err) {
      setContactNote(friendlyError(err.message) || t("contact.err"), "error");
      await prepareContactForm();
    } finally {
      contactSubmit.disabled = false;
      contactSubmit.textContent = t("contact.submit");
    }
  });

  document.getElementById("contact-again")?.addEventListener("click", async () => {
    showContactForm();
    await prepareContactForm();
    document.getElementById("contact-name")?.focus();
  });
}

document.getElementById("request-volume")?.addEventListener("click", () => {
  setWorkspace(false);
});

function initProductNav() {
  const companiesSection = document.getElementById("companies");
  const navCompanies = document.querySelector('.site-nav-link[data-nav="companies"]');
  if (!companiesSection || !navCompanies) return;

  function setCompaniesNavActive(active) {
    navCompanies.classList.toggle("is-active", active);
    navCompanies.setAttribute("aria-current", active ? "page" : "false");
  }

  document.querySelectorAll('a[href="#companies"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      companiesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", "#companies");
      setCompaniesNavActive(true);
    });
  });

  if (location.hash === "#companies") {
    requestAnimationFrame(() => {
      companiesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      setCompaniesNavActive(true);
    });
  }

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setCompaniesNavActive(true);
          else if (location.hash !== "#companies") setCompaniesNavActive(false);
        });
      },
      { rootMargin: "-20% 0px -55% 0px", threshold: 0 }
    );
    observer.observe(companiesSection);
  }
}

initProductNav();
applyI18n();
