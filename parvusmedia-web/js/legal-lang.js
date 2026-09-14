(() => {
  const KEY = "pm_legal_lang";
  const params = new URLSearchParams(location.search);
  const fromQuery = params.get("lang");
  let lang =
    fromQuery === "en" || fromQuery === "es"
      ? fromQuery
      : localStorage.getItem(KEY) === "es"
        ? "es"
        : localStorage.getItem(KEY) === "en"
          ? "en"
          : "en";

  const copy = {
    en: { cta: "Talk to us", legal: "Legal Notice", privacy: "Privacy Policy" },
    es: { cta: "Habla con nosotros", legal: "Aviso legal", privacy: "Política de privacidad" },
  };

  function apply() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-legal-lang]").forEach((el) => {
      el.hidden = el.getAttribute("data-legal-lang") !== lang;
    });
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      const active = btn.dataset.lang === lang;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    const t = copy[lang];
    document.querySelectorAll("[data-i18n-cta]").forEach((el) => {
      el.textContent = t.cta;
    });
    document.querySelectorAll("[data-i18n-legal]").forEach((el) => {
      el.textContent = t.legal;
    });
    document.querySelectorAll("[data-i18n-privacy]").forEach((el) => {
      el.textContent = t.privacy;
    });
    const titleEl = document.querySelector(`[data-legal-lang="${lang}"] [data-page-title]`);
    if (titleEl) document.title = titleEl.getAttribute("data-page-title");
  }

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      lang = btn.dataset.lang === "es" ? "es" : "en";
      localStorage.setItem(KEY, lang);
      apply();
    });
  });

  apply();
})();
