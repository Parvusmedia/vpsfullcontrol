const IS_PANEL = document.body.classList.contains("product-salesnav-panel");

function redirectLegacyAppQueriesToPanel() {
  const params = new URLSearchParams(window.location.search);
  if (params.has("connected") || params.has("credits")) {
    window.location.replace(`/salesnav/panel/${window.location.search}`);
  }
}

function scrollPanelHash() {
  const hash = window.location.hash.replace("#", "");
  if (hash === "topup") {
    document.getElementById("topup")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

const I18N = {
  en: {
    "nav.companies": "Companies",
    "nav.salesnav": "Sales Navigator",
    "nav.panel": "My panel",
    "nav.faq": "FAQ",
    "faq.title": "FAQ — how it works",
    "faq.lede": "Step-by-step guide: panel, LinkedIn connection, credits and exports.",
    "faq.qSteps": "How does it work, step by step?",
    "faq.aSteps":
      '<ol><li><strong>Create your account</strong> — open <a href="/salesnav/panel/">My panel</a>, enter your work email and sign in (or create a password).</li><li><strong>Top up credits</strong> — from €20 (240 credits with the +20% bonus). Credits stay linked to your email.</li><li><strong>Connect LinkedIn</strong> — click <em>Connect LinkedIn</em> in the panel. We use secure hosted authentication; we never store your password. You need an active Sales Navigator seat on that account.</li><li><strong>Start an export</strong> — paste a Sales Navigator saved list or people-search URL, set max leads and pick options: Basic (always), Enriched and/or Mail.</li><li><strong>Download the CSV</strong> — we process in the background and email you when ready. Download from the tasks table in your panel.</li></ol>',
    "faq.qConnect": "How do I connect my LinkedIn / Sales Navigator account?",
    "faq.aConnect":
      "<p>You need export credits before the first connection. In your panel, click <strong>Connect LinkedIn</strong>.</p><p>You are redirected to a secure sign-in page (Unipile). Log in with the LinkedIn account that has Sales Navigator. When it succeeds, the panel shows <strong>Connected</strong> with your name.</p><p>We never see or store your LinkedIn password. If the badge later shows <strong>Not connected</strong>, click <strong>Reconnect</strong> — we reuse your existing seat.</p>",
    "faq.qCredits": "How are credits consumed?",
    "faq.aCredits":
      '<p>Credits are prepaid. You are charged only when an export <strong>completes successfully</strong>. The tasks table shows total credits and a usage breakdown per export.</p><ul><li><strong>Basic</strong> — 1 credit per profile exported.</li><li><strong>Enriched</strong> (optional) — +0.4 credits per profile (rounded up for the whole export).</li><li><strong>Mail</strong> (optional) — +1 credit per work email actually found — you only pay for hits.</li></ul><div class="faq-examples"><p><strong>Examples</strong></p><ul><li>50 profiles, Basic only → <strong>50 credits</strong></li><li>50 profiles + Enriched → 50 + 20 = <strong>70 credits</strong></li><li>50 profiles + 25 verified emails → 50 + 25 = <strong>75 credits</strong></li><li>100 profiles + Enriched + 30 emails → 100 + 40 + 30 = <strong>170 credits</strong></li></ul></div><p>If your balance is too low, the export is rejected <em>before</em> processing starts — top up and try again.</p>',
    "faq.qUrls": "Which URLs can I export?",
    "faq.aUrls":
      "<p>Paste the full browser URL while you are viewing the list or search in Sales Navigator:</p><ul><li><strong>Saved lead lists</strong> — <code>linkedin.com/sales/lists/people/…</code></li><li><strong>People searches</strong> — <code>linkedin.com/sales/search/people?…</code></li></ul><p>You must have access to that list or search on the LinkedIn account you connected. Copy the URL from the address bar — do not use a public LinkedIn profile URL.</p>",
    "faq.qWhenCharged": "When am I charged?",
    "faq.aWhenCharged":
      "<p>Credits are deducted when the export <strong>finishes successfully</strong> and the CSV is ready — not when you click <em>Start export</em>.</p><p>If an export fails (LinkedIn disconnected, invalid URL, insufficient credits, etc.), you are not charged for that run. Failed tasks show the reason in the panel.</p>",
    "faq.qDuration": "How long does an export take?",
    "faq.aDuration":
      "<p>Small lists (25–100 leads) with Basic only often finish in under a minute. Enriched adds company and profile data — large lists can take several minutes. Mail runs email discovery on top and may take longer still.</p><p>You can close the tab: we email you when the CSV is ready. Refresh the tasks table or follow the link in the email to download.</p>",
    "faq.qTopup": "How do top-ups and bonuses work?",
    "faq.aTopup":
      "<p>Minimum top-up is <strong>€20</strong>. Packs from 100 base credits include a <strong>+20% bonus</strong> (e.g. pay €20 → 240 credits).</p><p>Payment is via Stripe. Credits are linked to your work email — sign in with the same email on any device to see your balance. Top-ups do not expire while your account exists.</p>",
    "faq.qDisconnect": "LinkedIn shows as disconnected — what now?",
    "faq.aDisconnect":
      "<p>Sessions can expire after LinkedIn security checks or password changes. Click <strong>Reconnect</strong> in the panel and sign in again through the secure flow.</p><p>Exports in progress may fail if LinkedIn disconnects mid-run; reconnect and start a new export. Your credit balance is unchanged for failed runs.</p>",
    "faq.qMultiDevice": "Can I use the same credits on another computer?",
    "faq.aMultiDevice":
      "<p>Yes. Sign in to <a href=\"/salesnav/panel/\">My panel</a> with the same work email. Credits, LinkedIn connection and export history follow your account.</p><p>Only one active browser session is needed to start exports — you do not need to keep the tab open until completion.</p>",
    "faq.qLimits": "Are there export limits?",
    "faq.aLimits":
      "<p>Each export can request up to <strong>2,000 leads</strong>. LinkedIn also applies daily export caps per Sales Navigator seat (~2,000/day).</p><p>Enriched and Mail options increase processing time and credit cost but do not change the lead cap. For agencies with multiple SN seats, <a href=\"/salesnav/#pricing\">contact us</a> for multi-account setup.</p>",
    "panel.title": "My panel",
    "panel.lede": "Manage credits, LinkedIn connection and CSV exports.",
    "panel.exportTitle": "Export",
    "panel.creditsLabel": "Credits",
    "panel.topup": "Top up",
    "panel.tasksTitle": "Export tasks",
    "panel.tasksLede": "Paste a Sales Navigator list or search URL — we process it in the background and email you when ready.",
    "panel.newTask": "New export",
    "panel.startTask": "Start export",
    "panel.composeCancel": "Hide form",
    "tasks.colSource": "Source",
    "tasks.colStatus": "Status",
    "tasks.colLeads": "Leads",
    "tasks.colCredits": "Credits",
    "tasks.colCreated": "Created",
    "tasks.colAction": "Action",
    "tasks.empty": "No export tasks yet. Create one to process a lead list or search URL.",
    "tasks.processing": "Processing — your export will appear in the table once ready. We also emailed you a confirmation.",
    "tasks.status.processing": "Processing",
    "tasks.status.ready": "Ready",
    "tasks.status.failed": "Failed",
    "tasks.download": "Download CSV",
    "tasks.limitAll": "All",
    "form.limitAll": "All (up to 2,000)",
    "landing.openPanel": "Open my panel",
    "landing.getStarted": "Get started — from €20",
    "landing.panelNote": "After payment, manage credits, LinkedIn and exports in your private panel — not on this page.",
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
    "connect.reconnectHint": "We will reuse your existing LinkedIn seat — no new Unipile account.",
    "connect.disconnect": "Disconnect",
    "connect.reconnect": "Reconnect",
    "connect.expired":
      "Your LinkedIn connection expired. Reconnect to continue exporting.",
    "connect.copySeatId": "Copy",
    "connect.seatIdCopied": "Copied.",
    "connect.starting": "Opening secure connection…",
    "connect.success": "LinkedIn connected. You can export now.",
    "connect.failed": "Connection failed or was cancelled. Try again.",
    "connect.required": "Connect LinkedIn before exporting.",
    "connect.checking": "Checking…",
    "connect.checkingHint": "Verifying your LinkedIn link. This usually takes a few seconds.",
    "account.title": "Account",
    "account.signedIn": "Signed in",
    "account.emailLabel": "Email",
    "account.signIn": "Sign in",
    "account.signOut": "Sign out",
    "account.register": "Create account",
    "account.password": "Password",
    "account.passwordConfirm": "Confirm password",
    "account.registerNote": "We will email you a confirmation link before you can sign in.",
    "account.resendVerify": "Resend confirmation email",
    "account.verifySent": "Check your inbox to confirm your email before signing in.",
    "account.verifyOk": "Email confirmed. You are signed in.",
    "account.verifyFail": "Could not confirm your email. Request a new link.",
    "account.registerOk": "Account created. Check your inbox to confirm your email.",
    "account.registerReady": "Account created. You can sign in now.",
    "account.resendOk": "If an unconfirmed account exists for this email, we sent a new confirmation link.",
    "account.guestLead": "Enter your work email to manage credits and exports.",
    "account.stepEmail": "Step 1 · Work email",
    "account.stepPassword": "Step 2 · Sign in",
    "account.stepPasswordCopy": "Enter the password for {email}.",
    "account.stepLegacy": "Step 2 · Access your account",
    "account.stepLegacyCopy": "We found {count} credits linked to {email}. Continue without a password, or set one later from your panel.",
    "account.stepSetup": "Step 2 · Create account",
    "account.stepSetupCopy": "Create a password for {email} to save your credits and exports.",
    "account.stepVerify": "Step 2 · Confirm your email",
    "account.stepVerifyCopy": "We sent a confirmation link to {email}. Open it, then return here to sign in.",
    "account.continue": "Continue",
    "account.continuePanel": "Continue to panel",
    "account.forgotPassword": "Forgot password?",
    "account.forgotSent": "If an account exists for {email}, we sent reset instructions.",
    "account.stepForgot": "Password reset",
    "account.stepReset": "Step 2 · New password",
    "account.resetCopy": "Choose a new password for your account.",
    "account.resetOk": "Password updated. You are signed in.",
    "account.useAnotherEmail": "Use another email",
    "account.backToSignIn": "Back to sign in",
    "account.savePassword": "Save password & sign in",
    "account.signedInOk": "Signed in. Your credits and exports are linked to this email.",
    "account.signingIn": "Signing in…",
    "account.sessionExpired": "Your session expired. Sign in again to continue.",
    "account.signInRequired": "Sign in before topping up credits.",
    "credits.balance": "{count} export credits available",
    "credits.load": "Top up (from €20)",
    "credits.loadMore": "Load more credits",
    "credits.connectNeedsBalance": "Load credits first, then connect LinkedIn.",
    "credits.checkoutOpened": "Stripe checkout opened in a new window. Return here after payment.",
    "credits.confirmingPayment": "Confirming payment…",
    "credits.paidPending": "Payment received. Credits may take a few seconds — refresh if balance is still zero.",
    "credits.accountNote": "Credits are linked to your email. Sign in with the same email on any device to restore your balance.",
    "credits.email": "Work email",
    "credits.emailPlaceholder": "you@company.com",
    "credits.emailRequired": "Enter your work email before topping up.",
    "credits.accountLinked": "Account: {email}",
    "credits.paidWithEmail": "Payment confirmed — {count} credits added to {email}.",
    "credits.restoreToggle": "Already paid? Restore credits",
    "credits.restoreBtn": "Restore account",
    "credits.restored": "Account restored — {count} credits available.",
    "credits.restoreEmpty": "No credits found for this email yet.",
    "credits.pack": "Credit pack",
    "credits.paid": "Credits added. You can connect LinkedIn now.",
    "credits.cancelled": "Payment cancelled.",
    "credits.insufficient": "Not enough credits for this export. Top up from €20 (240 credits).",
    "credits.bonusNote": "Top-ups from 100 base credits include +20% bonus (e.g. pay €20 → 240 credits).",
    "mode.list": "Lead list",
    "mode.search": "People search",
    "form.listLabel": "Sales Navigator list URL",
    "form.listPlaceholder": "https://www.linkedin.com/sales/lists/people/…",
    "form.searchLabel": "Sales Navigator search URL",
    "form.searchPlaceholder": "https://www.linkedin.com/sales/search/people?…",
    "form.limit": "Max leads",
    "form.limit50": "50",
    "form.limit100": "100",
    "form.limit200": "200",
    "form.limit500": "500",
    "form.limit1000": "1,000",
    "form.tiers": "Export options",
    "form.tierEnriched": "Enriched (+€0.02/lead)",
    "form.tierMail": "Mail (+€0.09/email found)",
    "form.submit": "Export CSV",
    "form.hint":
      "Open your list in Sales Navigator, copy the browser URL and paste it above. Large lists may take a minute — keep this tab open.",
    "progress.label": "Exporting leads…",
    "progress.enriched": "Exporting and enriching profiles…",
    "results.title": "Export ready",
    "results.another": "Export another",
    "results.csv": "Download CSV",
    "results.agency": "Multi-account setup",
    "results.summary": "Exported {count} leads in {seconds}s ({credits} credits used · showing first 10).",
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
    "pricing.kicker": "Agencies & teams",
    "pricing.title": "Need more than one LinkedIn account?",
    "pricing.lede":
      "Most users top up credits and export on their own. If you are an agency or manage multiple Sales Navigator seats, contact us for a multi-account setup.",
    "pricing.b1": "Multiple LinkedIn / Sales Navigator seats",
    "pricing.b2": "Separate wallets per client or team member",
    "pricing.b3": "Agency billing and onboarding support",
    "contact.title": "Contact us",
    "contact.name": "Name",
    "contact.company": "Company / agency",
    "contact.email": "Corporate email",
    "contact.accounts": "LinkedIn / SN accounts needed",
    "contact.accountsPlaceholder": "Select…",
    "contact.accounts2": "2 accounts",
    "contact.accounts3_5": "3–5 accounts",
    "contact.accounts6_10": "6–10 accounts",
    "contact.accounts10plus": "10+ accounts",
    "contact.captcha": "Anti-spam",
    "contact.submit": "Send request",
    "contact.privacy":
      'We will only use these details to reply about multi-account Sales Navigator export. <a href="/privacy.html">Privacy policy</a>.',
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
      "Credits are consumed per export. LinkedIn daily export caps apply (~2,000/day per SN seat). Agencies with multiple accounts can contact us below.",
    "trust.privacy": "Terms & privacy policy",
    "footer.tag": "Company enrichment · Sales Navigator export",
    "footer.privacy": "Privacy",
    "msg.challenge": "Security check failed. Refresh the page and try again.",
    "msg.generic": "Something went wrong. Please try again.",
    "msg.rateLimit": "Rate limit reached. Try again later or contact us for multi-account setup.",
    "msg.empty": "No leads returned. Check the URL and Sales Navigator access.",
    "msg.exporting": "Exporting… this may take up to a minute for large lists.",
    "msg.exportingEnriched": "Exporting and enriching via Harvest… large lists may take several minutes.",
    "msg.contactOk": "Request sent. We will reply by email.",
  },
  es: {
    "nav.companies": "Empresas",
    "nav.salesnav": "Sales Navigator",
    "nav.panel": "Mi panel",
    "nav.faq": "FAQ",
    "faq.title": "FAQ — cómo funciona",
    "faq.lede": "Guía paso a paso: panel, conexión LinkedIn, créditos y exports.",
    "faq.qSteps": "¿Cómo funciona, paso a paso?",
    "faq.aSteps":
      '<ol><li><strong>Crea tu cuenta</strong> — abre <a href="/salesnav/panel/">Mi panel</a>, introduce tu email de trabajo e inicia sesión (o crea una contraseña).</li><li><strong>Recarga créditos</strong> — desde €20 (240 créditos con el bonus +20%). Los créditos quedan vinculados a tu email.</li><li><strong>Conecta LinkedIn</strong> — pulsa <em>Conectar LinkedIn</em> en el panel. Usamos autenticación segura alojada; no guardamos tu contraseña. Necesitas un seat activo de Sales Navigator.</li><li><strong>Inicia un export</strong> — pega la URL de una lista guardada o búsqueda de personas en Sales Navigator, elige el máximo de leads y las opciones: Basic (siempre), Enriched y/o Mail.</li><li><strong>Descarga el CSV</strong> — lo procesamos en segundo plano y te avisamos por email. Descarga desde la tabla de tareas en tu panel.</li></ol>',
    "faq.qConnect": "¿Cómo conecto mi cuenta LinkedIn / Sales Navigator?",
    "faq.aConnect":
      "<p>Necesitas créditos de export antes de la primera conexión. En el panel, pulsa <strong>Conectar LinkedIn</strong>.</p><p>Te redirigimos a una página de inicio de sesión segura (Unipile). Entra con la cuenta LinkedIn que tiene Sales Navigator. Al completarse, el panel muestra <strong>Conectado</strong> con tu nombre.</p><p>No vemos ni guardamos tu contraseña de LinkedIn. Si más tarde aparece <strong>Sin conectar</strong>, pulsa <strong>Reconectar</strong> — reutilizamos tu seat existente.</p>",
    "faq.qCredits": "¿Cómo se consumen los créditos?",
    "faq.aCredits":
      '<p>Los créditos son prepago. Solo se cobran cuando un export <strong>termina correctamente</strong>. La tabla de tareas muestra el total y el desglose de uso por export.</p><ul><li><strong>Basic</strong> — 1 crédito por perfil exportado.</li><li><strong>Enriched</strong> (opcional) — +0,4 créditos por perfil (redondeado al alza en el export).</li><li><strong>Mail</strong> (opcional) — +1 crédito por email de trabajo encontrado — solo pagas los aciertos.</li></ul><div class="faq-examples"><p><strong>Ejemplos</strong></p><ul><li>50 perfiles, solo Basic → <strong>50 créditos</strong></li><li>50 perfiles + Enriched → 50 + 20 = <strong>70 créditos</strong></li><li>50 perfiles + 25 emails verificados → 50 + 25 = <strong>75 créditos</strong></li><li>100 perfiles + Enriched + 30 emails → 100 + 40 + 30 = <strong>170 créditos</strong></li></ul></div><p>Si el saldo es insuficiente, el export se rechaza <em>antes</em> de procesar — recarga e inténtalo de nuevo.</p>',
    "faq.qUrls": "¿Qué URLs puedo exportar?",
    "faq.aUrls":
      "<p>Pega la URL completa del navegador mientras ves la lista o búsqueda en Sales Navigator:</p><ul><li><strong>Listas guardadas</strong> — <code>linkedin.com/sales/lists/people/…</code></li><li><strong>Búsquedas de personas</strong> — <code>linkedin.com/sales/search/people?…</code></li></ul><p>Debes tener acceso a esa lista o búsqueda en la cuenta LinkedIn conectada. Copia la URL de la barra de direcciones — no uses una URL pública de perfil.</p>",
    "faq.qWhenCharged": "¿Cuándo se me cobran los créditos?",
    "faq.aWhenCharged":
      "<p>Los créditos se descuentan cuando el export <strong>termina con éxito</strong> y el CSV está listo — no al pulsar <em>Iniciar export</em>.</p><p>Si falla (LinkedIn desconectado, URL inválida, créditos insuficientes, etc.), no se cobra esa ejecución. Las tareas fallidas muestran el motivo en el panel.</p>",
    "faq.qDuration": "¿Cuánto tarda un export?",
    "faq.aDuration":
      "<p>Listas pequeñas (25–100 leads) solo con Basic suelen tardar menos de un minuto. Enriched añade datos de empresa y perfil — listas grandes pueden tardar varios minutos. Mail busca emails encima y puede tardar más.</p><p>Puedes cerrar la pestaña: te avisamos por email cuando el CSV esté listo. Recarga la tabla de tareas o usa el enlace del email para descargar.</p>",
    "faq.qTopup": "¿Cómo funcionan las recargas y el bonus?",
    "faq.aTopup":
      "<p>La recarga mínima es <strong>€20</strong>. Los packs desde 100 créditos base incluyen <strong>+20% bonus</strong> (ej. pagas €20 → 240 créditos).</p><p>El pago es con Stripe. Los créditos van con tu email de trabajo — inicia sesión con el mismo email en cualquier dispositivo. No caducan mientras exista tu cuenta.</p>",
    "faq.qDisconnect": "LinkedIn aparece como desconectado — ¿qué hago?",
    "faq.aDisconnect":
      "<p>La sesión puede caducar tras controles de seguridad de LinkedIn o cambios de contraseña. Pulsa <strong>Reconectar</strong> en el panel y vuelve a iniciar sesión en el flujo seguro.</p><p>Los exports en curso pueden fallar si LinkedIn se desconecta a mitad — reconecta e inicia uno nuevo. El saldo no cambia en ejecuciones fallidas.</p>",
    "faq.qMultiDevice": "¿Puedo usar los mismos créditos en otro ordenador?",
    "faq.aMultiDevice":
      "<p>Sí. Inicia sesión en <a href=\"/salesnav/panel/\">Mi panel</a> con el mismo email de trabajo. Créditos, conexión LinkedIn e historial de exports siguen tu cuenta.</p><p>No hace falta mantener la pestaña abierta hasta que termine — solo para iniciar el export.</p>",
    "faq.qLimits": "¿Hay límites de export?",
    "faq.aLimits":
      "<p>Cada export puede pedir hasta <strong>2.000 leads</strong>. LinkedIn también aplica límites diarios por seat de Sales Navigator (~2.000/día).</p><p>Enriched y Mail aumentan tiempo y coste en créditos pero no el tope de leads. Para agencias con varios seats SN, <a href=\"/salesnav/#pricing\">contáctanos</a> para multi-cuenta.</p>",
    "panel.title": "Mi panel",
    "panel.lede": "Gestiona créditos, conexión LinkedIn y exports CSV.",
    "panel.exportTitle": "Exportar",
    "panel.creditsLabel": "Créditos",
    "panel.topup": "Recargar",
    "panel.tasksTitle": "Tareas de export",
    "panel.tasksLede": "Pega la URL de una lista o búsqueda de Sales Navigator — la procesamos en segundo plano y te avisamos por email.",
    "panel.newTask": "Nuevo export",
    "panel.startTask": "Iniciar export",
    "panel.composeCancel": "Ocultar formulario",
    "tasks.colSource": "Origen",
    "tasks.colStatus": "Estado",
    "tasks.colLeads": "Leads",
    "tasks.colCredits": "Créditos",
    "tasks.colCreated": "Creado",
    "tasks.colAction": "Acción",
    "tasks.empty": "Aún no hay tareas. Crea una para procesar una lista o URL de búsqueda.",
    "tasks.processing": "Procesando — el export aparecerá en la tabla cuando esté listo. También te enviamos un email de confirmación.",
    "tasks.status.processing": "Procesando",
    "tasks.status.ready": "Listo",
    "tasks.status.failed": "Fallido",
    "tasks.download": "Descargar CSV",
    "tasks.limitAll": "Todos",
    "form.limitAll": "Todos (hasta 2.000)",
    "landing.openPanel": "Abrir mi panel",
    "landing.getStarted": "Empezar — desde €20",
    "landing.panelNote": "Tras pagar, gestionas créditos, LinkedIn y exports en tu panel privado — no en esta página.",
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
    "connect.reconnectHint": "Reutilizaremos tu cuenta de LinkedIn existente — no creamos otra en Unipile.",
    "connect.disconnect": "Desconectar",
    "connect.reconnect": "Reconectar",
    "connect.expired":
      "Tu conexión con LinkedIn expiró. Reconecta para seguir exportando.",
    "connect.copySeatId": "Copiar",
    "connect.seatIdCopied": "Copiado.",
    "connect.starting": "Abriendo conexión segura…",
    "connect.success": "LinkedIn conectado. Ya puedes exportar.",
    "connect.failed": "Conexión fallida o cancelada. Inténtalo de nuevo.",
    "connect.required": "Conecta LinkedIn antes de exportar.",
    "connect.checking": "Comprobando…",
    "connect.checkingHint": "Verificando tu enlace de LinkedIn. Suele tardar unos segundos.",
    "account.title": "Cuenta",
    "account.signedIn": "Sesión iniciada",
    "account.emailLabel": "Email",
    "account.signIn": "Iniciar sesión",
    "account.signOut": "Cerrar sesión",
    "account.register": "Crear cuenta",
    "account.password": "Contraseña",
    "account.passwordConfirm": "Confirmar contraseña",
    "account.registerNote": "Te enviaremos un enlace de confirmación antes de poder iniciar sesión.",
    "account.resendVerify": "Reenviar email de confirmación",
    "account.verifySent": "Revisa tu bandeja de entrada y confirma tu email antes de iniciar sesión.",
    "account.verifyOk": "Email confirmado. Sesión iniciada.",
    "account.verifyFail": "No se pudo confirmar tu email. Solicita un enlace nuevo.",
    "account.registerOk": "Cuenta creada. Revisa tu email para confirmarla.",
    "account.registerReady": "Cuenta creada. Ya puedes iniciar sesión.",
    "account.resendOk": "Si existe una cuenta sin confirmar con este email, enviamos un enlace nuevo.",
    "account.guestLead": "Introduce tu email de trabajo para gestionar créditos y exports.",
    "account.stepEmail": "Paso 1 · Email de trabajo",
    "account.stepPassword": "Paso 2 · Iniciar sesión",
    "account.stepPasswordCopy": "Introduce la contraseña de {email}.",
    "account.stepLegacy": "Paso 2 · Acceder a tu cuenta",
    "account.stepLegacyCopy": "Encontramos {count} créditos vinculados a {email}. Puedes continuar sin contraseña o crear una después desde el panel.",
    "account.stepSetup": "Paso 2 · Crear cuenta",
    "account.stepSetupCopy": "Crea una contraseña para {email} y guarda tus créditos y exports.",
    "account.stepVerify": "Paso 2 · Confirma tu email",
    "account.stepVerifyCopy": "Enviamos un enlace de confirmación a {email}. Ábrelo y vuelve aquí para iniciar sesión.",
    "account.continue": "Continuar",
    "account.continuePanel": "Continuar al panel",
    "account.forgotPassword": "¿Olvidaste la contraseña?",
    "account.forgotSent": "Si existe una cuenta para {email}, enviamos instrucciones para restablecerla.",
    "account.stepForgot": "Restablecer contraseña",
    "account.stepReset": "Paso 2 · Nueva contraseña",
    "account.resetCopy": "Elige una contraseña nueva para tu cuenta.",
    "account.resetOk": "Contraseña actualizada. Sesión iniciada.",
    "account.useAnotherEmail": "Usar otro email",
    "account.backToSignIn": "Volver a iniciar sesión",
    "account.savePassword": "Guardar contraseña e iniciar sesión",
    "account.signedInOk": "Sesión iniciada. Tus créditos y exports quedan vinculados a este email.",
    "account.signingIn": "Iniciando sesión…",
    "account.sessionExpired": "Tu sesión expiró. Vuelve a iniciar sesión para continuar.",
    "account.signInRequired": "Inicia sesión antes de recargar créditos.",
    "credits.balance": "{count} créditos de export disponibles",
    "credits.load": "Recargar (desde €20)",
    "credits.loadMore": "Cargar más créditos",
    "credits.connectNeedsBalance": "Carga saldo primero y después conecta LinkedIn.",
    "credits.checkoutOpened": "Checkout de Stripe abierto. Vuelve aquí tras pagar.",
    "credits.confirmingPayment": "Confirmando pago…",
    "credits.paidPending": "Pago recibido. Los créditos pueden tardar unos segundos — recarga si el saldo sigue en cero.",
    "credits.accountNote": "Los créditos quedan vinculados a tu email. Inicia sesión con el mismo email en cualquier dispositivo para recuperar el saldo.",
    "credits.email": "Email de trabajo",
    "credits.emailPlaceholder": "tu@empresa.com",
    "credits.emailRequired": "Introduce tu email de trabajo antes de recargar.",
    "credits.accountLinked": "Cuenta: {email}",
    "credits.paidWithEmail": "Pago confirmado — {count} créditos añadidos a {email}.",
    "credits.restoreToggle": "¿Ya pagaste? Recuperar créditos",
    "credits.restoreBtn": "Recuperar cuenta",
    "credits.restored": "Cuenta recuperada — {count} créditos disponibles.",
    "credits.restoreEmpty": "No hay créditos para este email todavía.",
    "credits.pack": "Pack de créditos",
    "credits.paid": "Créditos añadidos. Ya puedes conectar LinkedIn.",
    "credits.cancelled": "Pago cancelado.",
    "credits.insufficient": "Créditos insuficientes para este export. Compra más (mín. €20).",
    "credits.bonusNote": "Recargas desde 100 créditos base incluyen +20% bonus (ej. pagas €20 → 240 créditos).",
    "mode.list": "Lista de leads",
    "mode.search": "Búsqueda de personas",
    "form.listLabel": "URL de lista Sales Navigator",
    "form.listPlaceholder": "https://www.linkedin.com/sales/lists/people/…",
    "form.searchLabel": "URL de búsqueda Sales Navigator",
    "form.searchPlaceholder": "https://www.linkedin.com/sales/search/people?…",
    "form.limit": "Máx. leads",
    "form.limit50": "50",
    "form.limit100": "100",
    "form.limit200": "200",
    "form.limit500": "500",
    "form.limit1000": "1.000",
    "form.tiers": "Opciones de export",
    "form.tierEnriched": "Enriched (+€0,02/lead)",
    "form.tierMail": "Mail (+€0,09/email encontrado)",
    "form.submit": "Exportar CSV",
    "form.hint":
      "Abre tu lista en Sales Navigator, copia la URL del navegador y pégala arriba. Listas grandes pueden tardar un minuto — no cierres esta pestaña.",
    "progress.label": "Exportando leads…",
    "progress.enriched": "Exportando y enriqueciendo perfiles…",
    "results.title": "Exportación lista",
    "results.another": "Exportar otra",
    "results.csv": "Descargar CSV",
    "results.agency": "Setup multi-cuenta",
    "results.summary": "Exportados {count} leads en {seconds}s ({credits} créditos usados · primeros 10).",
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
    "pricing.kicker": "Agencias y equipos",
    "pricing.title": "¿Necesitas más de una cuenta LinkedIn?",
    "pricing.lede":
      "La mayoría recarga créditos y exporta sola. Si eres agencia o gestionas varios seats de Sales Navigator, contáctanos para un setup multi-cuenta.",
    "pricing.b1": "Varios seats de LinkedIn / Sales Navigator",
    "pricing.b2": "Monederos separados por cliente o miembro del equipo",
    "pricing.b3": "Facturación para agencias y onboarding",
    "contact.title": "Contáctanos",
    "contact.name": "Nombre",
    "contact.company": "Empresa / agencia",
    "contact.email": "Email corporativo",
    "contact.accounts": "Cuentas LinkedIn / SN necesarias",
    "contact.accountsPlaceholder": "Selecciona…",
    "contact.accounts2": "2 cuentas",
    "contact.accounts3_5": "3–5 cuentas",
    "contact.accounts6_10": "6–10 cuentas",
    "contact.accounts10plus": "10+ cuentas",
    "contact.captcha": "Anti-spam",
    "contact.submit": "Enviar solicitud",
    "contact.privacy":
      'Solo usaremos estos datos para responder sobre export multi-cuenta de Sales Navigator. <a href="/privacy.html">Política de privacidad</a>.',
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
      "Los créditos se consumen por export. Aplican límites diarios de LinkedIn (~2.000/día por seat SN). Agencias con varias cuentas pueden contactarnos abajo.",
    "trust.privacy": "Términos y privacidad",
    "footer.tag": "Enriquecimiento de empresas · Export Sales Navigator",
    "footer.privacy": "Privacidad",
    "msg.challenge": "Falló la comprobación de seguridad. Recarga la página.",
    "msg.generic": "Algo salió mal. Inténtalo de nuevo.",
    "msg.rateLimit": "Límite de uso alcanzado. Prueba más tarde o contáctanos para multi-cuenta.",
    "msg.empty": "No se devolvieron leads. Revisa la URL y el acceso a Sales Navigator.",
    "msg.exporting": "Exportando… puede tardar hasta un minuto en listas grandes.",
    "msg.exportingEnriched": "Exportando y enriqueciendo con Harvest… listas grandes pueden tardar varios minutos.",
    "msg.contactOk": "Solicitud enviada. Responderemos por email.",
  },
};

let lang = "en";
let lastRows = [];
let lastExportTiers = { enriched: false, mail: false };

const BASIC_CSV_COLS = [
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

const ENRICHED_CSV_COLS = [
  "company_linkedin_url",
  "company_domain",
  "company_industry",
  "company_size",
  "company_hq",
  "seniority",
  "tenure_years",
  "profile_summary",
  "skills",
  "languages",
];
let contactChallengeToken = "";
let isConnected = false;
let reconnectAvailable = false;
let lastConnection = { connected: false, label: "", avatar_url: "", connected_at: "" };
let billingEnabled = false;
let creditBalance = 0;
let accountEmail = "";
let defaultPackId = "240";
let panelTasks = [];
let tasksPollTimer = null;
let composeOpen = false;
let connectionStatusLoading = false;

function setAuthSubmitLoading(loading, btn, idleKey = "") {
  if (!btn) return;
  btn.disabled = loading;
  if (loading) {
    if (!btn.dataset.idleLabel) btn.dataset.idleLabel = btn.textContent;
    btn.textContent = t("account.signingIn");
    return;
  }
  btn.textContent = btn.dataset.idleLabel || (idleKey ? t(idleKey) : btn.textContent);
  delete btn.dataset.idleLabel;
}

function setConnectionStatusLoading(loading) {
  connectionStatusLoading = loading;
  if (!IS_PANEL || !loading) return;

  const badge = document.getElementById("connect-badge");
  const copy = document.getElementById("connect-copy");
  const liCard = document.querySelector(".panel-card-linkedin");
  const billingActions = document.getElementById("connect-actions-billing");
  const connectedActions = document.getElementById("connect-actions-connected");
  const connectBtn = document.getElementById("connect-btn");
  const reconnectBtn = document.getElementById("reconnect-btn");
  const disconnectBtn = document.getElementById("disconnect-btn");
  const avatar = document.getElementById("connect-avatar");

  if (badge) {
    badge.dataset.state = "loading";
    badge.textContent = t("connect.checking");
  }
  if (copy) copy.textContent = t("connect.checkingHint");
  if (liCard) liCard.dataset.connected = "loading";
  if (billingActions) billingActions.hidden = true;
  if (connectedActions) connectedActions.hidden = true;
  if (connectBtn) {
    connectBtn.disabled = true;
    connectBtn.hidden = false;
  }
  if (reconnectBtn) reconnectBtn.disabled = true;
  if (disconnectBtn) disconnectBtn.disabled = true;
  if (avatar) {
    avatar.hidden = true;
    avatar.style.display = "none";
  }
  setExportGate(false);
}

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

function setNote(text, tone = "ok", scope = "auto") {
  const exportGateHidden = document.getElementById("export-gate")?.hidden !== false;
  let note;
  if (scope === "account") {
    note = document.getElementById("account-note");
  } else if (scope === "connect") {
    note = document.getElementById("connect-note");
  } else if (scope === "export") {
    note = document.getElementById("form-note");
  } else if (exportGateHidden) {
    note = document.getElementById("account-note") || document.getElementById("connect-note") || document.getElementById("form-note");
  } else {
    note = document.getElementById("form-note") || document.getElementById("account-note") || document.getElementById("connect-note");
  }
  if (!note) return;
  note.hidden = !text;
  note.dataset.tone = tone;
  note.textContent = text || "";
}

function setAccountNote(text, tone = "ok") {
  if (IS_PANEL) {
    const guestNote = document.getElementById("account-note-guest");
    const note = document.getElementById("account-note");
    const el = accountEmail ? note : guestNote || note;
    if (!el) return;
    el.hidden = !text;
    el.dataset.tone = tone;
    el.textContent = text || "";
    return;
  }
  setNote(text, tone, "account");
}

function setPanelFlash(text, tone = "ok") {
  const el = document.getElementById("panel-flash");
  if (!el) return;
  el.hidden = !text;
  el.dataset.tone = tone;
  el.textContent = text || "";
}

function setConnectNote(text, tone = "ok") {
  setNote(text, tone, "connect");
}

function setExportGate(visible) {
  const gate = document.getElementById("export-gate");
  if (gate) gate.hidden = !visible;
}

async function parseJsonResponse(res) {
  const text = await res.text();
  if (!text) {
    return {
      ok: false,
      error: res.ok ? "Empty server response." : `Request failed (${res.status}).`,
    };
  }
  try {
    return JSON.parse(text);
  } catch {
    return { ok: false, error: "Invalid server response." };
  }
}

function isLinkedInReconnectError(message) {
  const text = String(message || "").toLowerCase();
  return text.includes("reconnect your account") || text.includes("reconecta");
}

function renderConnectionStatus(data) {
  reconnectAvailable = !!data?.reconnect_available || !!data?.needs_reconnect;
  lastConnection = {
    connected: !!data?.connected,
    label: data?.label || data?.stored_label || "",
    avatar_url: data?.avatar_url || "",
    connected_at: data?.connected_at || "",
    needs_reconnect: !!data?.needs_reconnect,
    connect_message: data?.connect_message || "",
  };
  isConnected = lastConnection.connected;
  const badge = document.getElementById("connect-badge");
  const copy = document.getElementById("connect-copy");
  const avatar = document.getElementById("connect-avatar");
  const connectBtn = document.getElementById("connect-btn");
  const connectBtnDemo = document.getElementById("connect-btn-demo");
  const disconnectBtn = document.getElementById("disconnect-btn");
  const reconnectBtn = document.getElementById("reconnect-btn");
  const billingActions = document.getElementById("connect-actions-billing");
  const demoActions = document.getElementById("connect-actions-demo");
  const connectedActions = document.getElementById("connect-actions-connected");

  if (connectBtn) connectBtn.disabled = false;
  if (reconnectBtn) reconnectBtn.disabled = false;
  if (disconnectBtn) disconnectBtn.disabled = false;

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
    if (copy.hasAttribute("data-i18n")) {
      copy.innerHTML = t("connect.body");
    } else {
      copy.textContent = t("connect.body");
    }
  }

  if (avatar) {
    if (isConnected && data.avatar_url) {
      avatar.referrerPolicy = "no-referrer";
      avatar.src = data.avatar_url;
      avatar.alt = data.label ? `${data.label} profile photo` : "LinkedIn profile photo";
      avatar.hidden = false;
      avatar.style.display = "";
    } else {
      avatar.hidden = true;
      avatar.style.display = "none";
      avatar.removeAttribute("src");
      avatar.alt = "";
    }
  }

  if (billingActions) {
    billingActions.hidden = IS_PANEL ? isConnected : !billingEnabled || isConnected;
  }
  if (demoActions) demoActions.hidden = billingEnabled || isConnected;
  if (connectedActions) connectedActions.hidden = !isConnected;
  if (connectBtn) {
    connectBtn.hidden = isConnected;
    if (!isConnected) {
      connectBtn.textContent = reconnectAvailable ? t("connect.reconnect") : t("connect.cta");
    }
  }

  if (!isConnected && reconnectAvailable && copy) {
    const expiredMsg = data?.needs_reconnect
      ? t("connect.expired")
      : data?.connect_message || "";
    const hint = data?.stored_label
      ? t("connect.connectedAs", { label: data.stored_label }) + " — " + t("connect.reconnectHint")
      : t("connect.reconnectHint");
    copy.textContent = expiredMsg || hint;
  }

  const liCard = document.querySelector(".panel-card-linkedin");
  if (liCard) {
    liCard.dataset.connected = isConnected ? "true" : "false";
  }

  renderUnipileSeatInfo(data);

  setExportGate(isConnected);
  renderAccount();
}

function renderUnipileSeatInfo(data) {
  if (!IS_PANEL) return;
  const wrap = document.getElementById("unipile-seat-wrap");
  const idEl = document.getElementById("unipile-seat-id");
  if (!wrap || !idEl) return;

  const seatId = String(data?.unipile_account_id || "").trim();
  if (seatId === "") {
    wrap.hidden = true;
    idEl.textContent = "";
    return;
  }

  wrap.hidden = false;
  idEl.textContent = seatId;
}

async function copyUnipileSeatId() {
  const idEl = document.getElementById("unipile-seat-id");
  const text = idEl?.textContent?.trim() || "";
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    setConnectNote(t("connect.seatIdCopied"), "ok");
  } catch {
    setConnectNote(text, "ok");
  }
}

function renderAccount() {
  if (IS_PANEL) {
    renderPanelAccount();
    return;
  }

  const dashboard = document.getElementById("user-dashboard");
  const panel = document.getElementById("account-panel");
  const guestWrap = document.getElementById("account-guest-wrap");
  const memberWrap = document.getElementById("account-member-wrap");
  const balanceEl = document.getElementById("account-balance");
  const emailLine = document.getElementById("account-email-line");
  const packWrap = document.getElementById("account-pack-wrap");
  const buyBtn = document.getElementById("buy-credits-btn");
  const connectBtn = document.getElementById("connect-btn");

  if (!panel || !balanceEl) return;

  if (!billingEnabled) {
    if (dashboard) dashboard.hidden = true;
    if (connectBtn) {
      connectBtn.disabled = false;
      connectBtn.removeAttribute("aria-disabled");
    }
    return;
  }

  if (dashboard) dashboard.hidden = false;
  panel.hidden = false;

  const signedIn = !!accountEmail;
  if (guestWrap) guestWrap.hidden = signedIn;
  if (memberWrap) memberWrap.hidden = !signedIn;

  if (signedIn) {
    balanceEl.textContent = t("credits.balance", { count: creditBalance });
    if (emailLine) {
      emailLine.textContent = `${t("account.emailLabel")}: ${accountEmail}`;
    }
    if (packWrap) packWrap.hidden = false;
    if (buyBtn) {
      buyBtn.hidden = false;
      buyBtn.textContent = creditBalance > 0 ? t("credits.loadMore") : t("credits.load");
    }
  }

  const billingEmail = document.getElementById("billing-email");
  if (accountEmail) prefillAuthEmail(accountEmail);
  else if (billingEmail && !billingEmail.value) {
    const stored = readStoredAccountEmail();
    if (stored) billingEmail.value = stored;
  }

  const hasCredits = creditBalance > 0;
  if (connectBtn && !isConnected) {
    connectBtn.disabled = !hasCredits;
    connectBtn.setAttribute("aria-disabled", hasCredits ? "false" : "true");
  }
}

function renderPanelAccount() {
  const guestWrap = document.getElementById("panel-guest-wrap");
  const appWrap = document.getElementById("panel-app-wrap");
  const balanceEl = document.getElementById("toolbar-balance");
  const emailEl = document.getElementById("toolbar-email");
  const buyBtn = document.getElementById("buy-credits-btn");
  const connectBtn = document.getElementById("connect-btn");
  const packWrap = document.getElementById("credit-pack");

  const signedIn = billingEnabled && !!accountEmail;
  if (guestWrap) guestWrap.hidden = signedIn;
  if (appWrap) appWrap.hidden = !signedIn;

  if (balanceEl) balanceEl.textContent = String(creditBalance);
  if (emailEl) emailEl.textContent = accountEmail || "";
  if (buyBtn) {
    buyBtn.hidden = !billingEnabled;
    buyBtn.textContent = t("panel.topup");
  }

  const billingEmail = document.getElementById("billing-email");
  if (accountEmail) prefillAuthEmail(accountEmail);
  else if (billingEmail && !billingEmail.value) {
    const stored = readStoredAccountEmail();
    if (stored) billingEmail.value = stored;
  }

  const hasCredits = creditBalance > 0;
  if (connectBtn && !isConnected) {
    connectBtn.disabled = billingEnabled && !hasCredits;
    connectBtn.setAttribute("aria-disabled", connectBtn.disabled ? "true" : "false");
  }
}

function prefillAuthEmail(email) {
  if (!email) return;
  const authEmail = document.getElementById("auth-email");
  const billingEmail = document.getElementById("billing-email");
  if (authEmail && !authEmail.value) authEmail.value = email;
  if (billingEmail && !billingEmail.value) billingEmail.value = email;
}

let authPendingEmail = "";
let authPendingBalance = 0;
let authResetToken = "";

const AUTH_STEP_PANELS = ["password", "legacy", "setup", "verify", "forgot_sent", "reset"];

function setAuthStepLabel(key) {
  const label = document.getElementById("auth-step-label");
  if (label) label.textContent = t(key);
}

function hideAllAuthStepPanels() {
  AUTH_STEP_PANELS.forEach((name) => {
    const panel = document.getElementById(`auth-step-${name}`);
    if (panel) panel.hidden = true;
  });
}

function setAuthStep(step, email, balance = authPendingBalance) {
  authPendingEmail = email || authPendingEmail;
  authPendingBalance = balance;

  const emailForm = document.getElementById("auth-email-form");
  const backWrap = document.getElementById("auth-back-wrap");
  hideAllAuthStepPanels();

  if (step === "email") {
    if (emailForm) emailForm.hidden = false;
    if (backWrap) backWrap.hidden = true;
    setAuthStepLabel("account.stepEmail");
    return;
  }

  if (emailForm) emailForm.hidden = true;
  if (backWrap) backWrap.hidden = step === "reset";

  const panel = document.getElementById(`auth-step-${step}`);
  if (panel) panel.hidden = false;

  if (step === "password") {
    setAuthStepLabel("account.stepPassword");
    const copy = document.getElementById("auth-password-copy");
    if (copy) copy.textContent = t("account.stepPasswordCopy", { email: authPendingEmail });
    document.getElementById("auth-password")?.focus();
  } else if (step === "legacy") {
    setAuthStepLabel("account.stepLegacy");
    const copy = document.getElementById("auth-legacy-copy");
    if (copy) {
      copy.textContent = t("account.stepLegacyCopy", {
        email: authPendingEmail,
        count: authPendingBalance,
      });
    }
  } else if (step === "setup") {
    setAuthStepLabel("account.stepSetup");
    const copy = document.getElementById("auth-setup-copy");
    if (copy) copy.textContent = t("account.stepSetupCopy", { email: authPendingEmail });
    document.getElementById("auth-setup-password")?.focus();
  } else if (step === "verify") {
    setAuthStepLabel("account.stepVerify");
    const copy = document.getElementById("auth-verify-copy");
    if (copy) copy.textContent = t("account.stepVerifyCopy", { email: authPendingEmail });
  } else if (step === "forgot_sent") {
    setAuthStepLabel("account.stepForgot");
    const copy = document.getElementById("auth-forgot-copy");
    if (copy) copy.textContent = t("account.forgotSent", { email: authPendingEmail });
  } else if (step === "reset") {
    setAuthStepLabel("account.stepReset");
    document.getElementById("auth-reset-password")?.focus();
  }
}

async function continueAccount(email) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "continue", email }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  return data;
}

async function legacySignInAccount(email) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "legacy_signin", email }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  accountEmail = data.email || email;
  creditBalance = Number(data.balance) || 0;
  persistAccountEmail(accountEmail);
  renderAccount();
  if (IS_PANEL) {
    await refreshConnectionStatus();
    fetchTasks();
  } else {
    renderConnectionStatus(lastConnection);
  }
  if (creditBalance > 0) {
    setAccountNote(t("credits.restored", { count: creditBalance }), "ok");
  } else {
    setAccountNote(t("account.signedInOk"), "ok");
  }
  return data;
}

async function forgotPasswordAccount(email) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "forgot", email }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  return data;
}

async function resetPasswordAccount(token, password, passwordConfirm) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "reset",
      token,
      password,
      password_confirm: passwordConfirm,
    }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  accountEmail = data.email || accountEmail;
  creditBalance = Number(data.balance) || 0;
  if (accountEmail) persistAccountEmail(accountEmail);
  renderAccount();
  if (IS_PANEL) {
    await refreshConnectionStatus();
    fetchTasks();
  } else {
    renderConnectionStatus(lastConnection);
  }
  setAccountNote(t("account.resetOk"), "ok");
  return data;
}

function applyAuthContinueResult(data) {
  const step = data.next_step || "setup";
  const email = data.email || authPendingEmail;
  const balance = Number(data.balance) || 0;
  if (step === "password") setAuthStep("password", email, balance);
  else if (step === "legacy") setAuthStep("legacy", email, balance);
  else if (step === "verify_pending") setAuthStep("verify", email, balance);
  else setAuthStep("setup", email, balance);
}

async function continueFromEmailForm(ev) {
  if (ev?.preventDefault) ev.preventDefault();
  const email = (document.getElementById("auth-email")?.value || "").trim();
  if (!email) {
    setAccountNote(t("credits.emailRequired"), "error");
    document.getElementById("auth-email")?.focus();
    return;
  }
  const btn = document.getElementById("auth-continue-btn");
  if (btn) btn.disabled = true;
  try {
    const data = await continueAccount(email);
    applyAuthContinueResult(data);
    setAccountNote("", "ok");
  } catch (err) {
    setAccountNote(err.message || t("msg.generic"), "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function signInFromPasswordForm(ev) {
  if (ev?.preventDefault) ev.preventDefault();
  const email = authPendingEmail || (document.getElementById("auth-email")?.value || "").trim();
  const password = document.getElementById("auth-password")?.value || "";
  if (!email) {
    setAuthStep("email");
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  if (!password) {
    setAccountNote(t("account.password") + " required.", "error");
    document.getElementById("auth-password")?.focus();
    return;
  }
  const btn = document.querySelector("#auth-password-form button[type=submit]");
  setAuthSubmitLoading(true, btn, "account.signIn");
  try {
    await signInAccount(email, password);
  } catch (err) {
    if (err.needsVerification) {
      setAuthStep("verify", email);
    }
    setAccountNote(err.message || t("msg.generic"), "error");
  } finally {
    setAuthSubmitLoading(false, btn, "account.signIn");
  }
}

async function registerFromSetupForm(ev) {
  if (ev?.preventDefault) ev.preventDefault();
  const email = authPendingEmail || (document.getElementById("auth-email")?.value || "").trim();
  const password = document.getElementById("auth-setup-password")?.value || "";
  const passwordConfirm = document.getElementById("auth-setup-password-confirm")?.value || "";
  if (!email) {
    setAuthStep("email");
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  try {
    const data = await registerAccount(email, password, passwordConfirm);
    if (data.needs_verification) {
      setAuthStep("verify", email);
      setAccountNote(t("account.registerOk"), "ok");
    } else {
      await signInAccount(email, password, { silent: false });
    }
  } catch (err) {
    if (err.code === "email_exists") {
      setAuthStep("password", email);
    }
    setAccountNote(err.message || t("msg.generic"), "error");
  }
}

async function legacySignInFromPanel() {
  const email = authPendingEmail || (document.getElementById("auth-email")?.value || "").trim();
  if (!email) {
    setAuthStep("email");
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  const btn = document.getElementById("auth-legacy-btn");
  setAuthSubmitLoading(true, btn, "account.continuePanel");
  try {
    await legacySignInAccount(email);
  } catch (err) {
    if (err.message && err.message.includes("password")) {
      setAuthStep("password", email);
    }
    setAccountNote(err.message || t("msg.generic"), "error");
  } finally {
    setAuthSubmitLoading(false, btn, "account.continuePanel");
  }
}

async function forgotPasswordFromPanel() {
  const email = authPendingEmail || (document.getElementById("auth-email")?.value || "").trim();
  if (!email) {
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  try {
    await forgotPasswordAccount(email);
    setAuthStep("forgot_sent", email);
    setAccountNote("", "ok");
  } catch (err) {
    setAccountNote(err.message || t("msg.generic"), "error");
  }
}

async function resendVerificationFromPanel() {
  const email = authPendingEmail || (document.getElementById("auth-email")?.value || "").trim();
  if (!email) {
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  try {
    await resendVerificationEmail(email);
    setAccountNote(t("account.resendOk"), "ok");
  } catch (err) {
    setAccountNote(err.message || t("msg.generic"), "error");
  }
}

async function resetPasswordFromForm(ev) {
  if (ev?.preventDefault) ev.preventDefault();
  const password = document.getElementById("auth-reset-password")?.value || "";
  const passwordConfirm = document.getElementById("auth-reset-password-confirm")?.value || "";
  if (!authResetToken) {
    setAccountNote(t("msg.generic"), "error");
    return;
  }
  try {
    await resetPasswordAccount(authResetToken, password, passwordConfirm);
    authResetToken = "";
  } catch (err) {
    setAccountNote(err.message || t("msg.generic"), "error");
  }
}

function resetAuthFlow() {
  authPendingEmail = "";
  authPendingBalance = 0;
  setAuthStep("email");
  const pwd = document.getElementById("auth-password");
  const setupPwd = document.getElementById("auth-setup-password");
  const setupConfirm = document.getElementById("auth-setup-password-confirm");
  if (pwd) pwd.value = "";
  if (setupPwd) setupPwd.value = "";
  if (setupConfirm) setupConfirm.value = "";
}

function initAuthFlow() {
  setAuthStep("email");
}

async function handleResetQuery() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("reset");
  if (!token) return;
  params.delete("reset");
  const next = params.toString();
  const nextUrl = `${window.location.pathname}${next ? `?${next}` : ""}${window.location.hash}`;
  window.history.replaceState({}, "", nextUrl);
  authResetToken = token;
  const emailForm = document.getElementById("auth-email-form");
  if (emailForm) emailForm.hidden = true;
  hideAllAuthStepPanels();
  setAuthStep("reset");
}

function persistAccountEmail(email) {
  if (!email) return;
  try {
    localStorage.setItem("sn_account_email", email);
  } catch {
    /* ignore */
  }
}

function readStoredAccountEmail() {
  try {
    return (localStorage.getItem("sn_account_email") || "").trim();
  } catch {
    return "";
  }
}

function clearStoredAccountEmail() {
  try {
    localStorage.removeItem("sn_account_email");
  } catch {
    /* ignore */
  }
}

async function signInAccount(email, password, opts = {}) {
  const silent = !!opts.silent;
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "signin", email, password }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    const err = new Error(data.error || t("msg.generic"));
    err.code = data.code;
    err.needsVerification = !!data.needs_verification;
    throw err;
  }
  accountEmail = data.email || email;
  creditBalance = Number(data.balance) || 0;
  persistAccountEmail(accountEmail);
  renderAccount();
  if (IS_PANEL) {
    await refreshConnectionStatus();
    fetchTasks();
  } else {
    renderConnectionStatus(lastConnection);
  }
  if (!silent) {
    if (creditBalance > 0) {
      setAccountNote(t("credits.restored", { count: creditBalance }), "ok");
    } else {
      setAccountNote(t("account.signedInOk"), "ok");
    }
  }
  return data;
}

async function registerAccount(email, password, passwordConfirm) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "register",
      email,
      password,
      password_confirm: passwordConfirm,
    }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    const err = new Error(data.error || t("msg.generic"));
    err.code = data.code;
    throw err;
  }
  return data;
}

async function resendVerificationEmail(email) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "resend", email }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  return data;
}

async function verifyAccountToken(token) {
  const res = await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "verify", token }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  accountEmail = data.email || "";
  creditBalance = Number(data.balance) || 0;
  if (accountEmail) persistAccountEmail(accountEmail);
  renderAccount();
  if (IS_PANEL) {
    await refreshConnectionStatus();
    fetchTasks();
  } else {
    renderConnectionStatus(lastConnection);
  }
  return data;
}

function renderCredits() {
  renderAccount();
}

function renderCreditPacks(packs) {
  const select = document.getElementById("credit-pack");
  if (!select || !Array.isArray(packs) || !packs.length) return;
  const prev = select.value || defaultPackId;
  select.innerHTML = "";
  packs.forEach((pack) => {
    const opt = document.createElement("option");
    opt.value = String(pack.id);
    const price = pack.price_eur ? `€${pack.price_eur}` : "";
    opt.textContent = price ? `${pack.label} — ${price}` : pack.label;
    select.appendChild(opt);
  });
  if ([...select.options].some((o) => o.value === String(prev))) {
    select.value = String(prev);
  }
  defaultPackId = select.value || defaultPackId;
}

async function fetchCredits() {
  try {
    const res = await fetch("/api/salesnav-credits.php", { credentials: "same-origin" });
    const data = await parseJsonResponse(res);
    if (!res.ok || !data.ok) return;
    billingEnabled = !!data.billing_enabled;
    creditBalance = Number(data.balance) || 0;
    accountEmail = data.account_email || "";
    const storedEmail = readStoredAccountEmail();
    if (!accountEmail) {
      if (storedEmail) {
        prefillAuthEmail(storedEmail);
        if (IS_PANEL && billingEnabled) {
          setAccountNote(t("account.sessionExpired"), "error");
        }
      }
    } else {
      persistAccountEmail(accountEmail);
    }
    if (Array.isArray(data.packs) && data.packs.length) {
      renderCreditPacks(data.packs);
      const packSelect = document.getElementById("credit-pack");
      if (packSelect?.value) defaultPackId = packSelect.value;
    }
    renderCredits();
    if (!connectionStatusLoading) {
      renderConnectionStatus(lastConnection);
    }
    if (IS_PANEL && accountEmail) {
      fetchTasks();
    }
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

async function openStripePopup(url) {
  const features = "width=520,height=720,menubar=no,toolbar=no,location=yes,status=no,resizable=yes,scrollbars=yes";
  const popup = window.open(url, "salesnav_stripe", features);
  if (!popup) {
    window.location.href = url;
    return null;
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
      if (ev.data?.type !== "salesnav-stripe") return;
      finish(ev.data);
    };
    window.addEventListener("message", onMessage);
    const timer = setInterval(() => {
      if (popup.closed) finish({ ok: null });
    }, 500);
  });
}

async function startStripeCheckout(pack = defaultPackId) {
  const packSelect = document.getElementById("credit-pack");
  if (packSelect?.value) pack = packSelect.value;
  if (!accountEmail) {
    setAccountNote(t("account.signInRequired"), "error");
    if (IS_PANEL) {
      document.getElementById("panel-guest-wrap")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return;
  }
  try {
    sessionStorage.setItem("sn_pre_balance", String(creditBalance));
    sessionStorage.setItem("sn_checkout_email", accountEmail);
  } catch {
    /* ignore */
  }
  const res = await fetch("/api/salesnav-stripe-checkout.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pack, email: accountEmail }),
  });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok || !data.url) {
    throw new Error(data.error || t("msg.generic"));
  }
  persistAccountEmail(accountEmail);
  renderCredits();
  const result = await openStripePopup(data.url);
  if (result?.ok === true) {
    accountEmail = result.email || accountEmail;
    await fetchCredits();
    const added = Number(result.credits_added) || Math.max(0, creditBalance - (Number(sessionStorage.getItem("sn_pre_balance")) || 0));
    setAccountNote(t("credits.paidWithEmail", { count: added || creditBalance, email: accountEmail }), "ok");
    try {
      sessionStorage.removeItem("sn_pre_balance");
    } catch {
      /* ignore */
    }
    return;
  }
  if (result?.ok === false) {
    setAccountNote(t("credits.cancelled"), "error");
    return;
  }
  setAccountNote(t("credits.checkoutOpened"), "ok");
  await pollCreditsAfterReturn();
}

async function handleVerifyQuery() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("verify");
  if (!token) return;
  params.delete("verify");
  const next = params.toString();
  const nextUrl = `${window.location.pathname}${next ? `?${next}` : ""}${window.location.hash}`;
  window.history.replaceState({}, "", nextUrl);
  try {
    await verifyAccountToken(token);
    setAccountNote(t("account.verifyOk"), "ok");
  } catch (err) {
    setAccountNote(err.message || t("account.verifyFail"), "error");
  }
}

async function signOutAccount() {
  await fetch("/api/salesnav-account.php", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "signout", email: accountEmail || "x" }),
  });
  accountEmail = "";
  creditBalance = 0;
  clearStoredAccountEmail();
  renderAccount();
  renderConnectionStatus(lastConnection);
  setAccountNote("", "ok");
}

async function fetchConnectionStatus(options = {}) {
  const render = options.render !== false;
  const res = await fetch("/api/salesnav-status.php", { credentials: "same-origin" });
  const data = await parseJsonResponse(res);
  if (!res.ok || !data.ok) {
    throw new Error(data.error || t("msg.generic"));
  }
  if (render) renderConnectionStatus(data);
  return data;
}

async function syncConnectionFromStored(options = {}) {
  const render = options.render !== false;
  try {
    const res = await fetch("/api/salesnav-connect-sync.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await parseJsonResponse(res);
    if (res.ok && data.ok && data.connected) {
      return fetchConnectionStatus({ render });
    }
  } catch {
    /* fall through to status poll */
  }
  return null;
}

async function refreshConnectionStatus() {
  setConnectionStatusLoading(true);
  try {
    let data = await fetchConnectionStatus({ render: false });
    if (!data.connected) {
      await syncConnectionFromStored({ render: false });
      data = await fetchConnectionStatus({ render: false });
    }
    renderConnectionStatus(data);
    return data;
  } catch {
    try {
      await syncConnectionFromStored({ render: false });
      const data = await fetchConnectionStatus({ render: false });
      renderConnectionStatus(data);
      return data;
    } catch {
      renderConnectionStatus({ connected: false });
      return lastConnection;
    }
  } finally {
    connectionStatusLoading = false;
  }
}

async function pollConnectionStatus(attempts = 8, delayMs = 1500) {
  setConnectionStatusLoading(true);
  try {
    for (let i = 0; i < attempts; i += 1) {
      try {
        if (i === 0 || i === 2 || i === 4) {
          const synced = await syncConnectionFromStored({ render: false });
          if (synced?.connected) {
            renderConnectionStatus(synced);
            return synced;
          }
        }
        const data = await fetchConnectionStatus({ render: false });
        if (data.connected) {
          renderConnectionStatus(data);
          return data;
        }
      } catch {
        /* retry */
      }
      await new Promise((r) => setTimeout(r, delayMs));
    }
    renderConnectionStatus({ connected: false });
    return { connected: false };
  } finally {
    connectionStatusLoading = false;
  }
}

async function startConnect(reconnect = false) {
  const isReconnect = reconnect || reconnectAvailable;
  const btn = isReconnect && !reconnect
    ? document.getElementById("connect-btn") || document.getElementById("reconnect-btn")
    : reconnect
      ? document.getElementById("reconnect-btn")
      : document.getElementById("connect-btn") || document.getElementById("connect-btn-demo");
  if (btn) btn.disabled = true;
  setConnectNote(t("connect.starting"), "ok");
  try {
    if (!isReconnect && billingEnabled && creditBalance <= 0) {
      setAccountNote(t("credits.connectNeedsBalance"), "error");
      return;
    }
    const res = await fetch("/api/salesnav-connect.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reconnect: isReconnect }),
    });
    const data = await parseJsonResponse(res);
    if (res.status === 402 && data.needs_payment) {
      setAccountNote(t("credits.connectNeedsBalance"), "error");
      return;
    }
    if (!res.ok || !data.ok || !data.url) {
      throw new Error(data.error || t("msg.generic"));
    }
    const popupOk = await openAuthPopup(data.url, "salesnav-connect");
    const status = await pollConnectionStatus(12, 1500);
    if (status.connected) {
      setConnectNote(t("connect.success"), "ok");
    } else if (popupOk === false) {
      setConnectNote(t("connect.failed"), "error");
    } else if (popupOk === null && !status.connected) {
      setConnectNote(t("connect.failed"), "error");
    }
  } catch (err) {
    setConnectNote(err.message || t("msg.generic"), "error");
  } finally {
    if (btn) {
      btn.disabled = !isReconnect && billingEnabled && creditBalance <= 0;
      if (btn.id === "connect-btn") {
        btn.setAttribute("aria-disabled", btn.disabled ? "true" : "false");
      }
    }
  }
}

async function disconnectLinkedIn() {
  try {
    const res = await fetch("/api/salesnav-disconnect.php", {
      method: "POST",
      credentials: "same-origin",
    });
    const data = await parseJsonResponse(res);
    if (!res.ok || !data.ok) {
      throw new Error(data.error || t("msg.generic"));
    }
    renderConnectionStatus({ connected: false });
    setAccountNote("", "ok");
    setConnectNote("", "ok");
  } catch (err) {
    setAccountNote(err.message || t("msg.generic"), "error");
  }
}

function handleConnectQuery() {
  const params = new URLSearchParams(window.location.search);
  const connected = params.get("connected");
  if (connected === "1") {
    pollConnectionStatus().then((data) => {
      if (data.connected) {
        setConnectNote(t("connect.success"), "ok");
      } else {
        setConnectNote(t("connect.failed"), "error");
      }
    });
    params.delete("connected");
    const qs = params.toString();
    const next = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
    window.history.replaceState({}, "", next);
  } else if (connected === "0") {
    setConnectNote(t("connect.failed"), "error");
    params.delete("connected");
    const qs = params.toString();
    const next = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
    window.history.replaceState({}, "", next);
  }
}

function handleCreditsQuery() {
  const params = new URLSearchParams(window.location.search);
  const credits = params.get("credits");
  const sessionId = params.get("session_id") || "";
  if (credits === "1") {
    if (sessionId) {
      completeStripeReturn(sessionId);
    } else {
      pollCreditsAfterReturn();
    }
    params.delete("credits");
    params.delete("session_id");
    const qs = params.toString();
    window.history.replaceState({}, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
  } else if (credits === "0") {
    setAccountNote(t("credits.cancelled"), "error");
    params.delete("credits");
    const qs = params.toString();
    window.history.replaceState({}, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
  }
}

async function completeStripeReturn(sessionId) {
  setAccountNote(t("credits.confirmingPayment"), "ok");
  try {
    const res = await fetch("/api/salesnav-stripe-complete.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    const data = await parseJsonResponse(res);
    if (!res.ok || !data.ok) {
      await pollCreditsAfterReturn();
      return;
    }
    accountEmail = data.email || accountEmail;
    persistAccountEmail(accountEmail);
    creditBalance = Number(data.balance) || 0;
    renderCredits();
    renderConnectionStatus(lastConnection);
    const added = Number(data.credits_added) || 0;
    setAccountNote(
      accountEmail
        ? t("credits.paidWithEmail", { count: added || creditBalance, email: accountEmail })
        : t("credits.paid"),
      "ok"
    );
  } catch {
    await pollCreditsAfterReturn();
  }
}

async function pollCreditsAfterReturn(maxAttempts = 15, delayMs = 2000) {
  let prev = 0;
  try {
    prev = parseInt(sessionStorage.getItem("sn_pre_balance") || "0", 10) || 0;
  } catch {
    prev = 0;
  }
  setAccountNote(t("credits.confirmingPayment"), "ok");
  for (let i = 0; i < maxAttempts; i += 1) {
    await fetchCredits();
    if (creditBalance > prev) {
      try {
        sessionStorage.removeItem("sn_pre_balance");
      } catch {
        /* ignore */
      }
      const email = accountEmail || sessionStorage.getItem("sn_checkout_email") || "";
      setAccountNote(
        email ? t("credits.paidWithEmail", { count: creditBalance - prev, email }) : t("credits.paid"),
        "ok"
      );
      return;
    }
    await new Promise((r) => setTimeout(r, delayMs));
  }
  setAccountNote(t("credits.paidPending"), "ok");
}

function formatTaskDate(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(lang === "es" ? "es-ES" : "en-GB", {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso.slice(0, 16).replace("T", " ");
  }
}

function taskStatusLabel(status) {
  if (status === "ready") return t("tasks.status.ready");
  if (status === "failed") return t("tasks.status.failed");
  return t("tasks.status.processing");
}

function taskLimitLabel(task) {
  if (task.limit_label === "all") return t("tasks.limitAll");
  return String(task.limit || "—");
}

function scheduleTasksPoll() {
  if (tasksPollTimer) {
    clearInterval(tasksPollTimer);
    tasksPollTimer = null;
  }
  const hasProcessing = panelTasks.some((task) => task.status === "processing");
  if (hasProcessing) {
    tasksPollTimer = setInterval(() => {
      fetchTasks({ silent: true });
    }, 4000);
  }
}

async function fetchTasks(opts = {}) {
  if (!IS_PANEL || !accountEmail) return;
  try {
    const res = await fetch("/api/salesnav-tasks.php", { credentials: "same-origin" });
    const data = await parseJsonResponse(res);
    if (!res.ok || !data.ok) return;
    panelTasks = Array.isArray(data.tasks) ? data.tasks : [];
    renderTasksTable();
    scheduleTasksPoll();
    if (panelTasks.some((task) => task.status === "failed" && isLinkedInReconnectError(task.error))) {
      fetchConnectionStatus().catch(() => {});
    }
    if (!opts.silent) {
      highlightTaskFromQuery();
    }
  } catch {
    /* optional */
  }
}

function highlightTaskFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const taskId = params.get("task");
  if (!taskId) return;
  const row = document.querySelector(`tr[data-task-id="${CSS.escape(taskId)}"]`);
  if (row) {
    row.classList.add("tasks-row-highlight");
    row.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function renderTasksTable() {
  const tbody = document.getElementById("tasks-body");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (!panelTasks.length) {
    const tr = document.createElement("tr");
    tr.className = "tasks-empty";
    tr.id = "tasks-empty-row";
    const td = document.createElement("td");
    td.colSpan = 6;
    td.textContent = t("tasks.empty");
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  panelTasks.forEach((task) => {
    const tr = document.createElement("tr");
    tr.dataset.taskId = task.id;
    if (task.status === "processing") tr.classList.add("tasks-row-processing");
    if (task.status === "failed") tr.classList.add("tasks-row-failed");

    const source = document.createElement("td");
    source.textContent = task.source_label || task.mode || "—";

    const status = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "task-status";
    badge.dataset.status = task.status || "processing";
    badge.textContent = taskStatusLabel(task.status);
    if (task.status === "failed" && task.error) {
      badge.title = task.error;
    }
    status.appendChild(badge);

    const leads = document.createElement("td");
    leads.textContent = task.status === "ready" ? String(task.lead_count || 0) : "—";

    const credits = document.createElement("td");
    credits.textContent = task.status === "ready" ? String(task.credits_used || 0) : "—";

    const created = document.createElement("td");
    created.textContent = formatTaskDate(task.created_at);

    const action = document.createElement("td");
    if (task.download_ready) {
      const link = document.createElement("a");
      link.className = "ghost-btn tasks-download-btn";
      link.href = `/api/salesnav-tasks-download.php?id=${encodeURIComponent(task.id)}`;
      link.textContent = t("tasks.download");
      action.appendChild(link);
    } else if (task.status === "failed") {
      action.textContent = task.error || "—";
      action.className = "tasks-error-cell";
    } else {
      action.textContent = "…";
    }

    tr.append(source, status, leads, credits, created, action);
    tbody.appendChild(tr);
  });
}

function openCreateTaskCompose() {
  if (!accountEmail) {
    setAccountNote(t("credits.emailRequired"), "error");
    return;
  }
  if (!isConnected) {
    setConnectNote(t("connect.required"), "error");
    return;
  }
  const compose = document.getElementById("tasks-compose");
  if (!compose) return;
  compose.hidden = false;
  composeOpen = true;
  compose.scrollIntoView({ behavior: "smooth", block: "nearest" });
  document.getElementById("list-url")?.focus();
}

function closeCreateTaskCompose(clearForm = false) {
  const compose = document.getElementById("tasks-compose");
  if (!compose) return;
  compose.hidden = true;
  composeOpen = false;
  if (clearForm) {
    document.getElementById("create-task-form")?.reset();
    document.querySelector("#create-task-form .mode-btn[data-mode='list']")?.click();
  }
}

async function submitCreateTask(e) {
  e.preventDefault();
  if (!isConnected) {
    setConnectNote(t("connect.required"), "error");
    return;
  }

  const mode = document.querySelector("#create-task-form .mode-btn.is-active")?.dataset.mode || "list";
  const listUrl = document.getElementById("list-url")?.value.trim() || "";
  const searchUrl = document.getElementById("search-url")?.value.trim() || "";
  const limitRaw = document.getElementById("export-limit")?.value || "50";
  const honeypot = document.getElementById("company_url")?.value || "";
  const tierEnriched = document.getElementById("tier-enriched")?.checked;

  if (mode === "list" && !listUrl) {
    setPanelFlash(lang === "es" ? "Pega la URL de la lista." : "Paste a list URL.", "error");
    return;
  }
  if (mode === "search" && !searchUrl) {
    setPanelFlash(lang === "es" ? "Pega la URL de búsqueda." : "Paste a search URL.", "error");
    return;
  }

  const submitBtn = document.getElementById("create-task-submit");
  if (submitBtn) submitBtn.disabled = true;

  try {
    const challenge = await getChallenge();
    const body = {
      challenge,
      company_url: honeypot,
      limit: limitRaw,
      tier_enriched: tierEnriched ? 1 : 0,
    };
    if (mode === "list") body.list_url = listUrl;
    else body.search_url = searchUrl;

    const res = await fetch("/api/salesnav-tasks.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await parseJsonResponse(res);

    if (res.status === 402 && data.needs_payment) {
      const detail = data.error || t("credits.insufficient");
      throw new Error(detail);
    }
    if (data.needs_connect || data.needs_reconnect) {
      renderConnectionStatus({
        connected: false,
        reconnect_available: true,
        needs_reconnect: !!data.needs_reconnect,
        stored_label: data.stored_label || "",
        connect_message: data.error || "",
      });
      throw new Error(data.error || t("connect.required"));
    }
    if (!res.ok || !data.ok) {
      throw new Error(data.error || t("msg.generic"));
    }

    closeCreateTaskCompose(true);
    setPanelFlash(t("tasks.processing"), "ok");
    if (data.task) {
      panelTasks = [data.task, ...panelTasks.filter((item) => item.id !== data.task.id)];
      renderTasksTable();
      scheduleTasksPoll();
    } else {
      await fetchTasks();
    }
  } catch (err) {
    setPanelFlash(err.message || t("msg.generic"), "error");
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function setProgress(active, labelKey = "progress.label") {
  const progress = document.getElementById("progress");
  const label = document.getElementById("progress-label");
  if (label) label.textContent = t(labelKey);
  if (progress) progress.hidden = !active;
}

function csvEscape(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}

function csvColumnsForExport() {
  const cols = [...BASIC_CSV_COLS];
  if (lastExportTiers.enriched) {
    cols.push(...ENRICHED_CSV_COLS);
  }
  return cols;
}

function downloadCsv(rows) {
  const cols = csvColumnsForExport();
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
  const data = await parseJsonResponse(res);
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

  const tierEnriched = document.getElementById("tier-enriched")?.checked;
  const tierMail = document.getElementById("tier-mail")?.checked;

  setNote(tierEnriched ? t("msg.exportingEnriched") : t("msg.exporting"), "ok");
  setProgress(true, tierEnriched ? "progress.enriched" : "progress.label");
  document.getElementById("results")?.setAttribute("hidden", "");
  document.getElementById("export-submit").disabled = true;

  try {
    const challenge = await getChallenge();
    const body = {
      challenge,
      company_url: honeypot,
      limit,
      tier_enriched: tierEnriched ? 1 : 0,
      tier_mail: tierMail ? 1 : 0,
    };
    if (mode === "list") body.list_url = listUrl;
    else body.search_url = searchUrl;

    const res = await fetch("/api/salesnav-export.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await parseJsonResponse(res);

    if (res.status === 429) {
      throw new Error(t("msg.rateLimit"));
    }
    if (res.status === 402 && data.needs_payment) {
      await startStripeCheckout(defaultPackId);
      throw new Error(t("credits.insufficient"));
    }
    if (data.needs_connect || data.needs_reconnect) {
      renderConnectionStatus({
        connected: false,
        reconnect_available: true,
        needs_reconnect: !!data.needs_reconnect,
        stored_label: data.stored_label || "",
        connect_message: data.error || "",
      });
      throw new Error(data.error || t("connect.required"));
    }
    if (!res.ok || !data.ok) {
      throw new Error(data.error || t("msg.generic"));
    }

    lastRows = data.rows || [];
    lastExportTiers = {
      enriched: !!data.tiers?.enriched,
      mail: !!data.tiers?.mail,
    };
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
        credits: data.credits_used ?? data.count ?? lastRows.length,
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
  const root = document.getElementById("create-task-form") || document;
  root.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      root.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("is-active"));
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
  const data = await parseJsonResponse(res);
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
    const accounts = document.getElementById("contact-accounts")?.value || "";
    const message = `Sales Navigator multi-account · accounts: ${accounts}`;

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
          volume: accounts,
          message,
          source: "salesnav",
          challenge: contactChallengeToken,
          captcha_id: document.getElementById("captcha-id").value,
          captcha_answer: document.getElementById("captcha-answer").value.trim(),
          website: document.getElementById("contact-website").value,
        }),
      });
      const data = await parseJsonResponse(res);
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

if (IS_PANEL) {
  initPanelPage();
} else {
  redirectLegacyAppQueriesToPanel();
  initContactForm();
}

function initPanelPage() {
  initModeSwitch();
  initAuthFlow();
  handleVerifyQuery();
  handleResetQuery();
  handleConnectQuery();
  handleCreditsQuery();
  if (IS_PANEL) setConnectionStatusLoading(true);
  fetchCredits();
  refreshConnectionStatus().catch(() => {});
  scrollPanelHash();

  document.getElementById("credit-pack")?.addEventListener("change", (e) => {
    defaultPackId = e.target.value || defaultPackId;
  });
  document.getElementById("connect-btn")?.addEventListener("click", () => startConnect(false));
  document.getElementById("reconnect-btn")?.addEventListener("click", () => startConnect(true));
  document.getElementById("unipile-seat-copy")?.addEventListener("click", () => copyUnipileSeatId());
  document.getElementById("buy-credits-btn")?.addEventListener("click", async () => {
    try {
      const packSelect = document.getElementById("credit-pack");
      const pack = packSelect?.value || defaultPackId;
      await startStripeCheckout(pack);
    } catch (err) {
      setAccountNote(err.message || t("msg.generic"), "error");
    }
  });
  document.getElementById("auth-email-form")?.addEventListener("submit", (e) => continueFromEmailForm(e));
  document.getElementById("auth-password-form")?.addEventListener("submit", (e) => signInFromPasswordForm(e));
  document.getElementById("auth-setup-form")?.addEventListener("submit", (e) => registerFromSetupForm(e));
  document.getElementById("auth-reset-form")?.addEventListener("submit", (e) => resetPasswordFromForm(e));
  document.getElementById("auth-legacy-btn")?.addEventListener("click", () => legacySignInFromPanel());
  document.getElementById("auth-forgot-btn")?.addEventListener("click", () => forgotPasswordFromPanel());
  document.getElementById("auth-resend-btn")?.addEventListener("click", () => resendVerificationFromPanel());
  document.getElementById("auth-back-btn")?.addEventListener("click", () => resetAuthFlow());
  document.getElementById("auth-back-to-password-btn")?.addEventListener("click", () => setAuthStep("password", authPendingEmail));
  document.getElementById("sign-out-btn")?.addEventListener("click", () => {
    panelTasks = [];
    if (tasksPollTimer) {
      clearInterval(tasksPollTimer);
      tasksPollTimer = null;
    }
    signOutAccount();
  });
  document.getElementById("disconnect-btn")?.addEventListener("click", () => disconnectLinkedIn());
  document.getElementById("create-task-btn")?.addEventListener("click", () => {
    if (composeOpen) {
      document.getElementById("tasks-compose")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    openCreateTaskCompose();
  });
  document.getElementById("create-task-cancel")?.addEventListener("click", () => closeCreateTaskCompose(false));
  document.getElementById("create-task-form")?.addEventListener("submit", (e) => submitCreateTask(e));
}
