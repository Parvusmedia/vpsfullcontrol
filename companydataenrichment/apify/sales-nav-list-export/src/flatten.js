/**
 * Flatten Unipile lead payload to CDE / SalesNav CSV columns.
 * Mirrors cde_salesnav_flatten_lead() in public/api/_unipile.php
 */

/** @param {Record<string, unknown>} item */
export function flattenLead(item) {
  let company = item.company ?? {};
  if (typeof company === 'string') {
    company = { name: company };
  }
  if (!company || typeof company !== 'object') {
    company = {};
  }

  const positions = item.current_positions ?? item.positions ?? [];
  let role = '';
  let companyName = String(company.name ?? item.company_name ?? '');
  if (Array.isArray(positions) && positions[0] && typeof positions[0] === 'object') {
    const pos = /** @type {Record<string, unknown>} */ (positions[0]);
    role = String(pos.role ?? pos.title ?? '');
    if (!companyName) {
      companyName = String(pos.company ?? '');
    }
  }

  const name = String(item.name ?? '');
  const parts = name ? name.split(/\s+/, 2) : ['', ''];
  const first = String(item.first_name ?? parts[0] ?? '');
  const last = String(item.last_name ?? parts[1] ?? '');

  return {
    first_name: first,
    last_name: last,
    full_name: name || `${first} ${last}`.trim(),
    job_title: String(item.headline ?? role ?? item.title ?? ''),
    company_name: companyName,
    location: String(item.location ?? ''),
    linkedin_url: String(
      item.public_profile_url ?? item.profile_url ?? item.linkedin_url ?? '',
    ),
    sales_nav_id: String(item.id ?? item.member_id ?? ''),
    open_profile: String(item.open_profile ?? item.open_link ?? ''),
    connection_degree: String(item.network_distance ?? item.degree ?? ''),
  };
}

/** @param {Record<string, unknown>} page */
export function collectItems(page) {
  for (const key of ['items', 'data', 'results', 'leads']) {
    const value = page[key];
    if (Array.isArray(value)) {
      return value;
    }
  }
  return [];
}

/**
 * @param {string} value
 * @param {'list' | 'search'} mode
 */
export function normalizeSourceUrl(value, mode) {
  const trimmed = value.trim();
  if (mode === 'list') {
    const listMatch = trimmed.match(
      /https?:\/\/(?:www\.)?linkedin\.com\/sales\/lists\/people\/\d+/i,
    );
    if (listMatch) {
      return listMatch[0];
    }
    if (/^\d+$/.test(trimmed)) {
      return `https://www.linkedin.com/sales/lists/people/${trimmed}`;
    }
    throw new Error('Invalid Sales Navigator list URL or list id.');
  }

  if (!/linkedin\.com\/sales\/search\/people/i.test(trimmed)) {
    throw new Error('Invalid Sales Navigator search URL.');
  }
  return trimmed;
}

/**
 * @param {string} baseUrl
 */
export function detectApiVersion(baseUrl) {
  const base = baseUrl.replace(/\/$/, '');
  return (
    base.includes('/api/v1')
    || (!base.endsWith('/v2') && !base.includes('api.unipile.com/v2'))
  );
}

/**
 * @param {() => Promise<void>} fn
 * @param {number} ms
 */
export async function sleep(ms) {
  if (ms <= 0) return;
  await new Promise((resolve) => setTimeout(resolve, ms));
}
