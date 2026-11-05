/**
 * Ngaged panel onboarding — lightweight spotlight tour (no dependencies).
 */
(function () {
  const STORAGE_PANEL = 'ngaged_tour_panel_v1';
  const STORAGE_CAMPAIGN = 'ngaged_tour_campaign_v1';

  let ctx = {};
  let active = null;
  let highlightEl = null;
  let backdrop = null;
  let popover = null;

  function $(sel) {
    return document.querySelector(sel);
  }

  function readFlag(key) {
    try {
      return localStorage.getItem(key) || '';
    } catch {
      return '';
    }
  }

  function writeFlag(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch {
      /* ignore */
    }
  }

  function clearHighlight() {
    if (highlightEl) {
      highlightEl.classList.remove('onboarding-highlight');
      highlightEl = null;
    }
  }

  function destroyUi() {
    clearHighlight();
    backdrop?.remove();
    popover?.remove();
    backdrop = null;
    popover = null;
    document.body.classList.remove('onboarding-active');
    active = null;
  }

  function ensureUi() {
    if (backdrop) return;
    backdrop = document.createElement('div');
    backdrop.className = 'onboarding-backdrop';
    backdrop.setAttribute('aria-hidden', 'true');
    popover = document.createElement('div');
    popover.className = 'onboarding-popover';
    popover.setAttribute('role', 'dialog');
    popover.setAttribute('aria-modal', 'true');
    document.body.appendChild(backdrop);
    document.body.appendChild(popover);
  }

  function openSidebarIfNeeded(el) {
    if (!el?.closest?.('#admin-sidebar')) return;
    if (window.matchMedia('(max-width: 991.98px)').matches) {
      const sidebar = $('#admin-sidebar');
      if (sidebar && !sidebar.classList.contains('is-open')) {
        sidebar.classList.add('is-open');
        const overlay = $('#sidebar-overlay');
        if (overlay) {
          overlay.hidden = false;
          overlay.classList.add('is-visible');
          overlay.setAttribute('aria-hidden', 'false');
        }
        document.body.classList.add('sidebar-nav-open');
      }
    }
  }

  function positionPopover(target, placement) {
    const pad = 12;
    const popRect = popover.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    if (!target || placement === 'center') {
      popover.style.left = Math.max(pad, (vw - popRect.width) / 2) + 'px';
      popover.style.top = Math.max(pad, (vh - popRect.height) / 2) + 'px';
      return;
    }

    const rect = target.getBoundingClientRect();
    let top = rect.bottom + pad;
    let left = rect.left;

    if (placement === 'top') {
      top = rect.top - popRect.height - pad;
    }
    if (placement === 'left') {
      left = rect.left - popRect.width - pad;
      top = rect.top;
    }
    if (placement === 'right') {
      left = rect.right + pad;
      top = rect.top;
    }

    if (left + popRect.width > vw - pad) left = vw - popRect.width - pad;
    if (left < pad) left = pad;
    if (top + popRect.height > vh - pad) top = Math.max(pad, rect.top - popRect.height - pad);
    if (top < pad) top = pad;

    popover.style.left = left + 'px';
    popover.style.top = top + 'px';
  }

  async function prepareStep(step) {
    if (step.panel && ctx.navigateTo) {
      ctx.navigateTo(step.panel);
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    }
    let target = null;
    if (step.target) {
      target = $(step.target);
      if (target) {
        openSidebarIfNeeded(target);
        target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        await new Promise((r) => setTimeout(r, 280));
      }
    }
    return target;
  }

  function renderPopover(step, index, total, target) {
    const isLast = index >= total - 1;
    const isFirst = index === 0;
    popover.innerHTML =
      '<div class="onboarding-popover-inner">' +
      '<p class="onboarding-step-label">Paso ' +
      (index + 1) +
      ' de ' +
      total +
      '</p>' +
      '<h2 class="onboarding-title h6">' +
      escapeHtml(step.title) +
      '</h2>' +
      '<p class="onboarding-body small text-muted mb-0">' +
      escapeHtml(step.body) +
      '</p>' +
      '<div class="onboarding-actions">' +
      '<button type="button" class="btn btn-link btn-sm onboarding-skip">Omitir</button>' +
      '<div class="d-flex gap-2">' +
      (isFirst ? '' : '<button type="button" class="btn btn-outline-secondary btn-sm onboarding-prev">Anterior</button>') +
      '<button type="button" class="btn btn-primary btn-sm onboarding-next">' +
      (isLast ? (step.finishLabel || 'Empezar') : 'Siguiente') +
      '</button>' +
      '</div></div></div>';

    popover.querySelector('.onboarding-skip')?.addEventListener('click', () => finishTour('skipped'));
    popover.querySelector('.onboarding-prev')?.addEventListener('click', () => go(-1));
    popover.querySelector('.onboarding-next')?.addEventListener('click', () => {
      if (isLast) finishTour('done');
      else go(1);
    });
    positionPopover(target, step.placement || (target ? 'bottom' : 'center'));
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  async function showStep() {
    if (!active) return;
    const { steps, index } = active;
    const step = steps[index];
    clearHighlight();
    const target = await prepareStep(step);
    if (step.target && !target) {
      go(1);
      return;
    }
    if (target) {
      target.classList.add('onboarding-highlight');
      highlightEl = target;
    }
    renderPopover(step, index, steps.length, target);
    requestAnimationFrame(() => positionPopover(target, step.placement || (target ? 'bottom' : 'center')));
  }

  function go(delta) {
    if (!active) return;
    active.index += delta;
    if (active.index < 0) active.index = 0;
    if (active.index >= active.steps.length) {
      finishTour('done');
      return;
    }
    showStep();
  }

  function finishTour(status) {
    const storageKey = active?.storageKey;
    if (storageKey) writeFlag(storageKey, status);
    const onDone = active?.onDone;
    destroyUi();
    if (status === 'done' && typeof onDone === 'function') onDone();
  }

  function startTour(config) {
    destroyUi();
    if (!config.steps?.length) return;
    ensureUi();
    document.body.classList.add('onboarding-active');
    active = {
      steps: config.steps,
      index: 0,
      storageKey: config.storageKey || null,
      onDone: config.onDone || null,
    };
    showStep();
  }

  function panelSteps(full) {
    const steps = [
      {
        title: 'Bienvenido a Ngaged',
        body: 'Amplifica posts de LinkedIn con tu equipo: campañas por email, repost con un clic y métricas en el dashboard.',
        placement: 'center',
      },
      {
        panel: 'dashboard',
        target: '#tour-dashboard-section',
        title: 'Dashboard',
        body: 'KPIs de campañas, adopción y reposts. Si aún no hay envíos, verás una guía para crear la primera campaña.',
        placement: 'bottom',
      },
      {
        target: '.sidebar-link[data-panel="campaigns"]',
        title: 'Crear y enviar',
        body: 'Pega la URL del post de LinkedIn, revisa la vista previa, elige destinatarios y envía la campaña.',
        placement: 'right',
      },
    ];
    if (full) {
      steps.push({
        target: '.sidebar-link[data-panel="members"]',
        title: 'Miembros del equipo',
        body: 'Alta manual o invitación LinkedIn. Sin miembros no hay destinatarios para las campañas.',
        placement: 'right',
      });
      steps.push({
        target: '#settings-panel-access',
        panel: 'settings',
        title: 'Accesos al panel',
        body: 'Como administrador puedes dar acceso a managers (solo campañas) u otros administradores.',
        placement: 'bottom',
      });
    } else {
      steps.push({
        target: '.sidebar-link[data-panel="campaigns-history"]',
        title: 'Historial',
        body: 'Consulta campañas enviadas y resultados. Los managers no gestionan miembros ni invitaciones.',
        placement: 'right',
      });
    }
    steps.push({
      title: 'Listo para empezar',
      body: full
        ? 'Siguiente paso recomendado: añade miembros o lanza tu primera campaña. Puedes repetir este tour en Ajustes.'
        : 'Abre Crear y enviar y sigue el mini-tour de campaña. Repite el tour en Ajustes cuando quieras.',
      placement: 'center',
      finishLabel: full ? 'Ir a campañas' : 'Ir a campañas',
    });
    return steps;
  }

  function campaignSteps() {
    return [
      {
        panel: 'campaigns',
        target: '#camp-url',
        title: 'URL del post',
        body: 'Copia el enlace del post de LinkedIn de tu empresa. Pulsa Vista previa para cargar título e imagen.',
        placement: 'bottom',
      },
      {
        target: '#camp-preview-btn',
        title: 'Vista previa',
        body: 'Valida que el post es el correcto antes de enviar.',
        placement: 'bottom',
      },
      {
        target: '#camp-member-picks',
        title: 'Destinatarios',
        body: 'Marca personas o equipos. Solo reciben email quienes selecciones aquí.',
        placement: 'top',
      },
      {
        target: '#camp-submit-btn',
        title: 'Enviar',
        body: 'Guarda la campaña y dispara los emails con Repostear / Ignorar. Luego mira el dashboard.',
        placement: 'top',
        finishLabel: 'Entendido',
      },
    ];
  }

  function maybeStartPanelTour(admin) {
    if (readFlag(STORAGE_PANEL)) return;
    const full = ctx.isFullAdmin?.(admin) ?? true;
    setTimeout(() => {
      startTour({
        storageKey: STORAGE_PANEL,
        steps: panelSteps(full),
        onDone: () => ctx.navigateTo?.('campaigns'),
      });
    }, 600);
  }

  function maybeStartCampaignTour() {
    if (readFlag(STORAGE_CAMPAIGN)) return;
    setTimeout(() => {
      startTour({
        storageKey: STORAGE_CAMPAIGN,
        steps: campaignSteps(),
      });
    }, 400);
  }

  window.NgagedOnboarding = {
    init(options) {
      ctx = options || {};
    },
    maybeStartPanelTour,
    maybeStartCampaignTour,
    startPanelTour: () => {
      writeFlag(STORAGE_PANEL, '');
      maybeStartPanelTour(ctx.currentAdmin?.() ?? null);
    },
  };

  window.addEventListener('resize', () => {
    if (active) showStep();
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && active) finishTour('skipped');
  });
})();
