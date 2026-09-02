/**
 * HarvestAPI profile enrichment — mirrors public/api/_harvest.php (CDE Enriched tier).
 * Docs: https://docs.harvestapi.io/linkedin-api-reference/profile/get
 */

/** @typedef {{ apiKey: string, baseUrl: string, timeoutMs: number, profileMain: boolean }} HarvestConfig */

/**
 * @param {string} [apiKey]
 * @param {string} [baseUrl]
 */
export function createHarvestConfig(apiKey = '', baseUrl = 'https://api.harvestapi.io') {
  return {
    apiKey: apiKey.trim(),
    baseUrl: baseUrl.replace(/\/$/, ''),
    timeoutMs: Math.max(5000, Number(process.env.HARVEST_API_TIMEOUT ?? 25000)),
    profileMain: (process.env.HARVEST_PROFILE_MAIN ?? '1') !== '0',
  };
}

/**
 * @param {HarvestConfig} cfg
 * @param {string} path
 * @param {Record<string, string>} query
 */
async function harvestRequest(cfg, path, query) {
  const url = new URL(cfg.baseUrl + path);
  for (const [key, value] of Object.entries(query)) {
    url.searchParams.set(key, value);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), cfg.timeoutMs);
  try {
    const response = await fetch(url, {
      headers: {
        Accept: 'application/json',
        'X-API-Key': cfg.apiKey,
      },
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data.message ?? data.error ?? 'Harvest API error';
      throw new Error(String(message));
    }
    const element = data.element;
    if (!element || typeof element !== 'object') {
      throw new Error('Harvest response missing element');
    }
    return element;
  } finally {
    clearTimeout(timer);
  }
}

/** @param {string | undefined | null} website */
export function domainFromWebsite(website) {
  const raw = String(website ?? '').trim();
  if (!raw) return '';
  try {
    const href = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
    const host = new URL(href).hostname;
    return host.replace(/^www\./i, '');
  } catch {
    return '';
  }
}

/** @param {string | undefined | null} duration */
export function parseTenureYears(duration) {
  const text = String(duration ?? '').trim();
  const yrs = text.match(/(\d+)\s*yrs?/i) ?? text.match(/(\d+)\s*years?/i);
  return yrs ? yrs[1] : '';
}

/** @param {string | undefined | null} position */
export function inferSeniority(position) {
  const text = String(position ?? '').toLowerCase().trim();
  if (!text) return '';
  const map = [
    ['chief', 'C-Level'],
    ['ceo', 'C-Level'],
    ['cto', 'C-Level'],
    ['cfo', 'C-Level'],
    ['coo', 'C-Level'],
    ['co-founder', 'Founder'],
    ['founder', 'Founder'],
    ['president', 'President'],
    ['vice president', 'VP'],
    ['vp ', 'VP'],
    ['head of', 'Director'],
    ['director', 'Director'],
    ['manager', 'Manager'],
    ['senior', 'Senior'],
    ['lead', 'Lead'],
    ['intern', 'Intern'],
  ];
  for (const [needle, label] of map) {
    if (text.includes(needle)) return label;
  }
  return '';
}

/** @param {Record<string, unknown>} profile */
export function joinSkills(profile) {
  /** @type {string[]} */
  const names = [];
  for (const skill of profile.skills ?? []) {
    if (skill && typeof skill === 'object' && skill.name) {
      names.push(String(skill.name));
    } else if (typeof skill === 'string' && skill) {
      names.push(skill);
    }
  }
  if (!names.length && Array.isArray(profile.topSkills)) {
    for (const skill of profile.topSkills) {
      if (typeof skill === 'string' && skill) names.push(skill);
    }
  }
  return [...new Set(names)].slice(0, 25).join('; ');
}

/** @param {Record<string, unknown>} profile */
export function joinLanguages(profile) {
  /** @type {string[]} */
  const parts = [];
  for (const lang of profile.languages ?? []) {
    if (!lang || typeof lang !== 'object') continue;
    const name = String(lang.name ?? '').trim();
    if (!name) continue;
    const prof = String(lang.proficiency ?? '').trim();
    parts.push(prof ? `${name} (${prof})` : name);
  }
  return parts.join('; ');
}

/** @param {Record<string, unknown>} company */
export function companySize(company) {
  const range = company.employeeCountRange;
  if (range && typeof range === 'object') {
    const start = range.start ?? null;
    const end = range.end ?? null;
    if (start != null && end != null) return `${start}-${end}`;
    if (start != null) return `${start}+`;
  }
  if (company.employeeCount != null && company.employeeCount !== '') {
    return String(company.employeeCount);
  }
  return '';
}

/** @param {Record<string, unknown>} company */
export function companyHq(company) {
  for (const loc of company.locations ?? []) {
    if (!loc || typeof loc !== 'object') continue;
    if (loc.headquarter) {
      const parsed = loc.parsed?.text;
      if (typeof parsed === 'string' && parsed) return parsed;
      const bits = [loc.city, loc.geographicArea, loc.country].filter(Boolean);
      if (bits.length) return bits.join(', ');
    }
  }
  const first = company.locations?.[0];
  if (first && typeof first === 'object') {
    return String(first.parsed?.text ?? first.city ?? '');
  }
  return '';
}

/** @param {Record<string, unknown>} company */
export function companyIndustry(company) {
  /** @type {string[]} */
  const names = [];
  for (const ind of company.industries ?? []) {
    if (!ind || typeof ind !== 'object') continue;
    const name = ind.name ?? ind.title;
    if (name) names.push(String(name));
  }
  return [...new Set(names)].join('; ');
}

/**
 * @param {Record<string, unknown>} profile
 * @param {Record<string, unknown> | null | undefined} company
 * @param {Record<string, unknown>} experience
 */
export function mapEnrichedFields(profile, company, experience) {
  const position = String(experience.position ?? profile.headline ?? '');
  const companyUrl = String(experience.companyLinkedinUrl ?? '');
  const website = company && typeof company === 'object' ? String(company.website ?? '') : '';

  return {
    company_linkedin_url: companyUrl,
    company_domain: domainFromWebsite(website),
    company_industry: company ? companyIndustry(company) : '',
    company_size: company ? companySize(company) : '',
    company_hq: company ? companyHq(company) : '',
    seniority: inferSeniority(position),
    tenure_years: parseTenureYears(String(experience.duration ?? '')),
    profile_summary: String(profile.about ?? '').trim(),
    skills: joinSkills(profile),
    languages: joinLanguages(profile),
  };
}

/** @param {Record<string, unknown>} profile */
function primaryExperience(profile) {
  const experience = profile.experience?.[0] ?? profile.currentPosition?.[0];
  return experience && typeof experience === 'object' ? experience : {};
}

/**
 * @param {HarvestConfig} cfg
 * @param {string} linkedinUrl
 */
export async function fetchProfile(cfg, linkedinUrl) {
  const query = { url: linkedinUrl };
  if (cfg.profileMain) query.main = 'true';
  return harvestRequest(cfg, '/linkedin/profile', query);
}

/**
 * @param {HarvestConfig} cfg
 * @param {string} companyUrl
 */
export async function fetchCompany(cfg, companyUrl) {
  return harvestRequest(cfg, '/linkedin/company', { url: companyUrl });
}

/**
 * @param {Array<Record<string, string>>} rows
 * @param {HarvestConfig} cfg
 * @param {{ batchSize?: number, onProgress?: (done: number, total: number) => void }} [opts]
 */
export async function enrichRows(rows, cfg, opts = {}) {
  if (!rows.length || !cfg.apiKey) {
    return rows;
  }

  const batchSize = Math.max(3, Math.min(15, Number(opts.batchSize ?? process.env.HARVEST_BATCH_SIZE ?? 10)));
  const total = rows.length;
  /** @type {Array<Record<string, unknown> | null>} */
  const profiles = new Array(total).fill(null);

  /** @type {Array<{ index: number, url: string }>} */
  const jobs = [];
  rows.forEach((row, index) => {
    const url = String(row.linkedin_url ?? '').trim();
    if (url) jobs.push({ index, url });
  });

  for (let i = 0; i < jobs.length; i += batchSize) {
    const chunk = jobs.slice(i, i + batchSize);
    const results = await Promise.allSettled(
      chunk.map(({ url }) => fetchProfile(cfg, url)),
    );
    chunk.forEach(({ index }, j) => {
      const result = results[j];
      profiles[index] = result.status === 'fulfilled' ? result.value : null;
    });
    opts.onProgress?.(Math.min(i + chunk.length, jobs.length), jobs.length);
  }

  /** @type {Map<string, Record<string, unknown>>} */
  const companyCache = new Map();
  /** @type {Set<string>} */
  const companyUrls = new Set();
  for (const profile of profiles) {
    if (!profile) continue;
    const exp = primaryExperience(profile);
    const url = String(exp.companyLinkedinUrl ?? '').trim();
    if (url) companyUrls.add(url);
  }

  const companyList = [...companyUrls];
  for (let i = 0; i < companyList.length; i += batchSize) {
    const chunk = companyList.slice(i, i + batchSize);
    const results = await Promise.allSettled(
      chunk.map((url) => fetchCompany(cfg, url)),
    );
    chunk.forEach((url, j) => {
      const result = results[j];
      if (result.status === 'fulfilled') {
        companyCache.set(url, result.value);
      }
    });
  }

  return rows.map((row, index) => {
    const profile = profiles[index];
    if (!profile) return row;
    const experience = primaryExperience(profile);
    const companyUrl = String(experience.companyLinkedinUrl ?? '').trim();
    const company = companyUrl ? companyCache.get(companyUrl) ?? null : null;
    return { ...row, ...mapEnrichedFields(profile, company, experience) };
  });
}
