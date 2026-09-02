import { Actor } from 'apify';
import { flattenLead, normalizeSourceUrl } from './flatten.js';
import { createConfig, exportLeads } from './unipile.js';

await Actor.main(async () => {
  const input = await Actor.getInput() ?? {};

  const mode = input.mode === 'search' ? 'search' : 'list';
  const maxLeads = Math.max(1, Math.min(2000, Number(input.maxLeads ?? 100)));
  const pageDelayMs = Math.max(0, Number(input.pageDelayMs ?? 1500));

  const apiKey = String(input.unipileApiKey ?? process.env.UNIPILE_API_KEY ?? '').trim();
  const accountId = String(input.unipileAccountId ?? process.env.UNIPILE_ACCOUNT_ID ?? '').trim();
  const baseUrl = String(input.unipileBaseUrl ?? process.env.UNIPILE_BASE_URL ?? 'https://api.unipile.com/v2').trim();

  if (!apiKey) {
    throw new Error('Missing Unipile API key. Set unipileApiKey input or UNIPILE_API_KEY env var.');
  }
  if (!accountId) {
    throw new Error('Missing Unipile account ID. Set unipileAccountId input or UNIPILE_ACCOUNT_ID env var.');
  }

  const rawUrl = mode === 'search'
    ? String(input.searchUrl ?? '').trim()
    : String(input.listUrl ?? '').trim();

  if (!rawUrl) {
    throw new Error(mode === 'search'
      ? 'searchUrl is required when mode is search.'
      : 'listUrl is required when mode is list.');
  }

  const sourceUrl = normalizeSourceUrl(rawUrl, mode);
  const config = createConfig(baseUrl, apiKey, accountId);

  await Actor.setValue('INPUT_META', {
    mode,
    sourceUrl,
    maxLeads,
    accountId,
    apiVersion: config.isV1 ? 'v1' : 'v2',
    startedAt: new Date().toISOString(),
  });

  Actor.log.info(`Exporting up to ${maxLeads} leads from ${sourceUrl} (${mode}, Unipile ${config.isV1 ? 'v1' : 'v2'})`);

  const rawLeads = await exportLeads(config, sourceUrl, mode, maxLeads, pageDelayMs);
  const dataset = await Actor.openDataset();

  let pushed = 0;
  for (const row of rawLeads) {
    await dataset.pushData(flattenLead(row));
    pushed += 1;
  }

  await Actor.setValue('OUTPUT', {
    ok: true,
    mode,
    sourceUrl,
    requested: maxLeads,
    exported: pushed,
    finishedAt: new Date().toISOString(),
  });

  Actor.log.info(`Done. Exported ${pushed} leads.`);
});
