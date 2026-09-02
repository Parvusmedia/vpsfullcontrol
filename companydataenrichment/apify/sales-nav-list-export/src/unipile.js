import { collectItems, detectApiVersion, sleep } from './flatten.js';

/**
 * @typedef {Object} UnipileConfig
 * @property {string} apiKey
 * @property {string} accountId
 * @property {string} baseUrl
 * @property {boolean} isV1
 */

/**
 * @param {string} baseUrl
 * @param {string} apiKey
 * @param {string} accountId
 * @returns {UnipileConfig}
 */
export function createConfig(baseUrl, apiKey, accountId) {
  const normalizedBase = baseUrl.replace(/\/$/, '');
  return {
    apiKey,
    accountId,
    baseUrl: normalizedBase,
    isV1: detectApiVersion(normalizedBase),
  };
}

/**
 * @param {UnipileConfig} config
 * @param {string} method
 * @param {string} path
 * @param {Record<string, string | number> | null} [query]
 * @param {Record<string, unknown> | null} [body]
 */
async function unipileRequest(config, method, path, query = null, body = null) {
  let url = `${config.baseUrl}${path}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      params.set(key, String(value));
    }
    url += `?${params.toString()}`;
  }

  /** @type {RequestInit} */
  const init = {
    method,
    headers: {
      'X-API-KEY': config.apiKey,
      Accept: 'application/json',
    },
  };

  if (body !== null) {
    init.headers = {
      ...init.headers,
      'Content-Type': 'application/json',
    };
    init.body = JSON.stringify(body);
  }

  const response = await fetch(url, init);
  const raw = await response.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    const message = data.title ?? data.error ?? data.message ?? 'Unipile API error';
    const err = new Error(String(message));
    err.status = response.status;
    throw err;
  }

  return data;
}

/**
 * @param {UnipileConfig} config
 * @param {string} sourceUrl
 * @param {number} maxLeads
 * @param {number} pageDelayMs
 */
async function paginateV1(config, sourceUrl, maxLeads, pageDelayMs) {
  /** @type {Record<string, unknown>[]} */
  const collected = [];
  let cursor = null;

  while (collected.length < maxLeads) {
    const pageSize = Math.min(25, maxLeads - collected.length);
    /** @type {Record<string, string | number>} */
    const query = {
      account_id: config.accountId,
      limit: pageSize,
    };
    if (cursor) {
      query.cursor = cursor;
    }

    const data = await unipileRequest(config, 'POST', '/linkedin/search', query, {
      url: sourceUrl,
    });
    const batch = collectItems(data);
    if (!batch.length) break;

    for (const row of batch) {
      if (row && typeof row === 'object') {
        collected.push(/** @type {Record<string, unknown>} */ (row));
      }
    }

    cursor = data.cursor ?? data.next_cursor ?? null;
    if (!cursor) break;
    await sleep(pageDelayMs);
  }

  return collected.slice(0, maxLeads);
}

/**
 * @param {UnipileConfig} config
 * @param {string} searchUrl
 * @param {number} maxLeads
 * @param {number} pageDelayMs
 */
async function paginateV2Search(config, searchUrl, maxLeads, pageDelayMs) {
  /** @type {Record<string, unknown>[]} */
  const collected = [];
  let cursor = null;
  const limit = Math.min(100, maxLeads);

  while (collected.length < maxLeads) {
    /** @type {Record<string, string | number>} */
    const query = { limit };
    if (cursor) {
      query.cursor = cursor;
    }

    const data = await unipileRequest(
      config,
      'POST',
      `/${encodeURIComponent(config.accountId)}/linkedin/sales-navigator/search`,
      query,
      { url: searchUrl },
    );

    const batch = collectItems(data);
    if (!batch.length) break;

    for (const row of batch) {
      if (row && typeof row === 'object') {
        collected.push(/** @type {Record<string, unknown>} */ (row));
      }
    }

    cursor = data.next_cursor ?? data.cursor ?? null;
    if (!cursor || batch.length < limit) break;
    await sleep(pageDelayMs);
  }

  return collected.slice(0, maxLeads);
}

/**
 * @param {UnipileConfig} config
 * @param {string} listId
 * @param {number} maxLeads
 * @param {number} pageDelayMs
 */
async function paginateV2List(config, listId, maxLeads, pageDelayMs) {
  /** @type {Record<string, unknown>[]} */
  const collected = [];
  let offset = 0;
  const limit = Math.min(100, maxLeads);

  while (collected.length < maxLeads) {
    const data = await unipileRequest(
      config,
      'POST',
      `/${encodeURIComponent(config.accountId)}/linkedin/sales-navigator/lead-lists/${encodeURIComponent(listId)}`,
      { limit, offset },
      {},
    );

    const batch = collectItems(data);
    if (!batch.length) break;

    for (const row of batch) {
      if (row && typeof row === 'object') {
        collected.push(/** @type {Record<string, unknown>} */ (row));
      }
    }

    offset += batch.length;
    if (batch.length < limit) break;
    await sleep(pageDelayMs);
  }

  return collected.slice(0, maxLeads);
}

/**
 * @param {UnipileConfig} config
 * @param {string} sourceUrl
 * @param {'list' | 'search'} mode
 * @param {number} maxLeads
 * @param {number} pageDelayMs
 */
export async function exportLeads(config, sourceUrl, mode, maxLeads, pageDelayMs) {
  if (config.isV1) {
    return paginateV1(config, sourceUrl, maxLeads, pageDelayMs);
  }

  if (mode === 'search') {
    return paginateV2Search(config, sourceUrl, maxLeads, pageDelayMs);
  }

  const listMatch = sourceUrl.match(/linkedin\.com\/sales\/lists\/people\/(?<id>\d+)/i);
  if (listMatch?.groups?.id) {
    return paginateV2List(config, listMatch.groups.id, maxLeads, pageDelayMs);
  }

  return paginateV2Search(config, sourceUrl, maxLeads, pageDelayMs);
}
